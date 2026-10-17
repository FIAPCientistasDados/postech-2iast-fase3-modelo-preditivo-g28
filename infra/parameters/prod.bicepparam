using '../main.bicep'


// Ambiente e localização
param environment = 'prod'
param location = 'eastus'

// Nomes dos recursos
param dataFactoryName = 'adf-fiap-techchallenge'
param storageAccountName = 'stfiaptechchallenge'
param bronzeContainer = 'bronze'

// Credenciais e chaves
param googleApplicationCredentials = '/dbfs/FileStore/credenciais/gcp.json'
param keyVaultName = 'kvfiaptechprod'
