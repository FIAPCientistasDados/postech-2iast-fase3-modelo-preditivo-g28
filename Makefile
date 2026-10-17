# =========================
# Azure Bicep - Tech Challenge Fase 2
# =========================

-include .env
export


# =========================
# Configurações Azure
# =========================

RESOURCE_GROUP := rg-fiap-techchallenge-prod
LOCATION := eastus

MAIN_BICEP := infra/main.bicep
PARAMETERS := infra/parameters/prod.bicepparam

STORAGE_ACCOUNT := stfiapoin4ci2kb4w7c
AZURE_KEYVAULT_NAME := kvfiaptechprod

SUBSCRIPTION_ID := e4285dee-2708-4d00-b7a5-9c45f1f37e89

# Application ID do Service Principal de deploy.
SP_APP_ID := 3686488a-04fc-4d8a-b967-61f98ec41efe

# Object ID da aplicação empresarial AzureDatabricks.
DATABRICKS_AZURE_OBJECT_ID := 1d773a1f-1e5e-48d6-9a74-27e94d371bdc


# =========================
# Configurações Databricks
# =========================

# Caminho de destino do arquivo no workspace.
DATABRICKS_JOB_PATH := /Workspace/Users/rm374990@fiap.com.br/postech-aisc-fase-2-pipeline-azure-g23/jobs/main.py

# ID numérico do job Databricks.
# Deve vir do .env.
DATABRICKS_JOB_ID := $(SPARK_JOB)


# =========================
# Targets
# =========================

.PHONY: \
	help \
	check-env \
	login \
	rg-create \
	rg-show \
	validate \
	what-if \
	deploy \
	destroy \
	storage-key \
	kv-role-assign \
	databricks-kv-role \
	sync-storage-secrets \
	list-resources \
	deploy-pipeline \
	upload-job \
	run-job


# Target padrão.
.DEFAULT_GOAL := help


# =========================
# Ajuda
# =========================

help:
	@echo "Comandos disponíveis:"
	@echo "  make check-env            - Valida variáveis obrigatórias"
	@echo "  make login                - Faz login com Service Principal"
	@echo "  make rg-create            - Cria o Resource Group"
	@echo "  make rg-show              - Mostra o Resource Group"
	@echo "  make validate             - Valida o deployment Bicep"
	@echo "  make what-if              - Simula o deployment"
	@echo "  make deploy               - Implanta infraestrutura e sincroniza acessos"
	@echo "  make kv-role-assign       - Concede acesso do SP ao Key Vault"
	@echo "  make databricks-kv-role   - Concede leitura do Key Vault ao AzureDatabricks"
	@echo "  make sync-storage-secrets - Atualiza Storage Account e chave no Key Vault"
	@echo "  make storage-key          - Mostra a chave da Storage Account"
	@echo "  make list-resources       - Lista os recursos implantados"
	@echo "  make deploy-pipeline      - Implanta os recursos definidos no Bicep"
	@echo "  make upload-job           - Importa jobs/main.py no workspace"
	@echo "  make run-job              - Executa o job Databricks"
	@echo "  make destroy              - Remove o Resource Group"


# =========================
# Verificar variáveis
# =========================

check-env:
	@test -n "$(AZURE_CLIENT_ID)" || \
		(echo "Erro: AZURE_CLIENT_ID não configurado."; exit 1)
	@test -n "$(AZURE_CLIENT_SECRET)" || \
		(echo "Erro: AZURE_CLIENT_SECRET não configurado."; exit 1)
	@test -n "$(AZURE_TENANT_ID)" || \
		(echo "Erro: AZURE_TENANT_ID não configurado."; exit 1)
	@test -n "$(AZURE_SUBSCRIPTION_ID)" || \
		(echo "Erro: AZURE_SUBSCRIPTION_ID não configurado."; exit 1)


# =========================
# Autenticação Azure
# =========================

login: check-env
	@echo "Autenticando no Azure..."
	@az login \
		--service-principal \
		--username "$(AZURE_CLIENT_ID)" \
		--password "$(AZURE_CLIENT_SECRET)" \
		--tenant "$(AZURE_TENANT_ID)" \
		--output none
	@az account set \
		--subscription "$(AZURE_SUBSCRIPTION_ID)"
	@az account show \
		--query "{subscription:name,id:id,tenant:tenantId}" \
		--output table


# =========================
# Resource Group
# =========================

rg-create: login
	@echo "Criando ou validando Resource Group..."
	@az group create \
		--name "$(RESOURCE_GROUP)" \
		--location "$(LOCATION)" \
		--output none
	@echo "Resource Group disponível: $(RESOURCE_GROUP)"


rg-show: login
	@az group show \
		--name "$(RESOURCE_GROUP)" \
		--output table


# =========================
# Bicep
# =========================

validate: login rg-create
	@echo "Compilando Bicep..."
	@az bicep build \
		--file "$(MAIN_BICEP)"
	@echo "Validando parâmetros Bicep..."
	@az bicep build-params \
		--file "$(PARAMETERS)" \
		--outfile /tmp/prod.parameters.json
	@echo "Validando deployment..."
	@az deployment group validate \
		--resource-group "$(RESOURCE_GROUP)" \
		--template-file "$(MAIN_BICEP)" \
		--parameters "$(PARAMETERS)" \
		--output table
	@rm -f /tmp/prod.parameters.json


what-if: login rg-create
	@echo "Executando análise what-if..."
	@az deployment group what-if \
		--resource-group "$(RESOURCE_GROUP)" \
		--template-file "$(MAIN_BICEP)" \
		--parameters "$(PARAMETERS)"


# =========================
# Deployment principal
# =========================

deploy: validate
	@echo "Executando deployment..."
	@az deployment group create \
		--resource-group "$(RESOURCE_GROUP)" \
		--template-file "$(MAIN_BICEP)" \
		--parameters "$(PARAMETERS)" \
		--output table
	@$(MAKE) kv-role-assign
	@$(MAKE) databricks-kv-role
	@$(MAKE) sync-storage-secrets
	@echo "Deployment concluído."


# Mantido como alias para compatibilidade.
deploy-pipeline: deploy
	@echo "Infraestrutura e pipeline implantados."


# =========================
# Key Vault RBAC
# =========================

kv-role-assign: login
	@echo "Configurando acesso do Service Principal ao Key Vault..."
	@KV_ID=$$(az keyvault show \
		--name "$(AZURE_KEYVAULT_NAME)" \
		--resource-group "$(RESOURCE_GROUP)" \
		--query id \
		--output tsv); \
	test -n "$$KV_ID" || \
		(echo "Erro: Key Vault não encontrado."; exit 1); \
	EXISTING=$$(az role assignment list \
		--assignee "$(SP_APP_ID)" \
		--scope "$$KV_ID" \
		--role "Key Vault Secrets Officer" \
		--query "length(@)" \
		--output tsv); \
	if [ "$$EXISTING" = "0" ]; then \
		az role assignment create \
			--role "Key Vault Secrets Officer" \
			--assignee "$(SP_APP_ID)" \
			--scope "$$KV_ID" \
			--output none; \
		echo "Permissão Key Vault Secrets Officer criada."; \
	else \
		echo "Permissão Key Vault Secrets Officer já existe."; \
	fi


databricks-kv-role: login
	@echo "Configurando leitura do Key Vault pelo AzureDatabricks..."
	@KV_ID=$$(az keyvault show \
		--name "$(AZURE_KEYVAULT_NAME)" \
		--resource-group "$(RESOURCE_GROUP)" \
		--query id \
		--output tsv); \
	test -n "$$KV_ID" || \
		(echo "Erro: Key Vault não encontrado."; exit 1); \
	EXISTING=$$(az role assignment list \
		--assignee-object-id "$(DATABRICKS_AZURE_OBJECT_ID)" \
		--scope "$$KV_ID" \
		--role "Key Vault Secrets User" \
		--query "length(@)" \
		--output tsv); \
	if [ "$$EXISTING" = "0" ]; then \
		az role assignment create \
			--assignee-object-id "$(DATABRICKS_AZURE_OBJECT_ID)" \
			--assignee-principal-type ServicePrincipal \
			--role "Key Vault Secrets User" \
			--scope "$$KV_ID" \
			--output none; \
		echo "Permissão Key Vault Secrets User criada."; \
	else \
		echo "Permissão Key Vault Secrets User já existe."; \
	fi


# =========================
# Sincronizar Storage e Key Vault
# =========================

sync-storage-secrets: login
	@echo "Sincronizando Storage Account com o Key Vault..."
	@STORAGE_NAME=$$(az storage account list \
		--resource-group "$(RESOURCE_GROUP)" \
		--query "[?name=='$(STORAGE_ACCOUNT)'].name | [0]" \
		--output tsv); \
	test -n "$$STORAGE_NAME" || \
		(echo "Erro: Storage Account $(STORAGE_ACCOUNT) não encontrada."; exit 1); \
	STORAGE_KEY=$$(az storage account keys list \
		--resource-group "$(RESOURCE_GROUP)" \
		--account-name "$$STORAGE_NAME" \
		--query "[?keyName=='key1'].value | [0]" \
		--output tsv); \
	test -n "$$STORAGE_KEY" || \
		(echo "Erro: key1 não foi recuperada."; exit 1); \
	az keyvault secret set \
		--vault-name "$(AZURE_KEYVAULT_NAME)" \
		--name "AZURE-STORAGE-ACCOUNT" \
		--value "$$STORAGE_NAME" \
		--output none; \
	az keyvault secret set \
		--vault-name "$(AZURE_KEYVAULT_NAME)" \
		--name "AZURE-STORAGE-KEY" \
		--value "$$STORAGE_KEY" \
		--output none; \
	unset STORAGE_KEY; \
	echo "Segredos sincronizados com $$STORAGE_NAME."


# =========================
# Storage
# =========================

storage-key: login
	@az storage account keys list \
		--resource-group "$(RESOURCE_GROUP)" \
		--account-name "$(STORAGE_ACCOUNT)" \
		--query "[0].value" \
		--output tsv


# =========================
# Recursos
# =========================

list-resources: login
	@az resource list \
		--resource-group "$(RESOURCE_GROUP)" \
		--output table


# =========================
# Databricks
# =========================

upload-job:
	@test -n "$(AZURE_DATABRICKS_HOST)" || \
		(echo "Erro: AZURE_DATABRICKS_HOST não configurado."; exit 1)
	@test -n "$(AZURE_DATABRICKS_TOKEN)" || \
		(echo "Erro: AZURE_DATABRICKS_TOKEN não configurado."; exit 1)
	@test -f "./jobs/main.py" || \
		(echo "Erro: ./jobs/main.py não encontrado."; exit 1)
	@echo "Importando jobs/main.py para o workspace..."
	@DATABRICKS_HOST="$(AZURE_DATABRICKS_HOST)" \
	DATABRICKS_TOKEN="$(AZURE_DATABRICKS_TOKEN)" \
	databricks workspace import \
		"$(DATABRICKS_JOB_PATH)" \
		--file "./jobs/main.py" \
		--language PYTHON \
		--format SOURCE \
		--overwrite
	@echo "Arquivo importado para $(DATABRICKS_JOB_PATH)."


run-job:
	@test -n "$(AZURE_DATABRICKS_HOST)" || \
		(echo "Erro: AZURE_DATABRICKS_HOST não configurado."; exit 1)
	@test -n "$(AZURE_DATABRICKS_TOKEN)" || \
		(echo "Erro: AZURE_DATABRICKS_TOKEN não configurado."; exit 1)
	@test -n "$(DATABRICKS_JOB_ID)" || \
		(echo "Erro: SPARK_JOB não configurado com o ID do job."; exit 1)
	@echo "Executando job $(DATABRICKS_JOB_ID)..."
	@DATABRICKS_HOST="$(AZURE_DATABRICKS_HOST)" \
	DATABRICKS_TOKEN="$(AZURE_DATABRICKS_TOKEN)" \
	databricks jobs run-now "$(DATABRICKS_JOB_ID)"


# =========================
# Destruição
# =========================

destroy: login
	@echo "Removendo Resource Group $(RESOURCE_GROUP)..."
	@az group delete \
		--name "$(RESOURCE_GROUP)" \
		--yes \
		--no-wait
	@echo "Solicitação de remoção enviada."