using '../main.bicep'

// =========================
// Ambiente e localização
// =========================

param environment = 'prod'
param location = 'eastus'


// =========================
// Nomes dos recursos
// =========================

param dataFactoryName = 'adf-fiap-techchallenge'

// Deve ser o nome da conta que já existe no Azure.
// Usar outro nome cria outra Storage Account.
param storageAccountName = 'stfiaptechchallenge2iast'

param bronzeContainer = 'bronze'

param keyVaultName = 'kvfiaptechprod'


// =========================
// Identidades para IAM
// =========================

// Object ID do Service Principal que executa o deployment.
// Não use o Application ID.
param deployServicePrincipalObjectId = '03c0bc6d-ff3c-4b1f-8ef7-1105abe6abb5'

// Object ID da aplicação empresarial AzureDatabricks.
param azureDatabricksObjectId = '1d773a1f-1e5e-48d6-9a74-27e94d371bdc'


// =========================
// Configuração Google
// =========================

// Caminho utilizado pelo código no Databricks.
// Este valor é um caminho, não o conteúdo da credencial.
param googleApplicationCredentials = '/dbfs/FileStore/credenciais/gcp.json'
