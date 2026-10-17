// =========================
// Parâmetros principais
// =========================
param environment string
param location string
param dataFactoryName string
param storageAccountName string
param bronzeContainer string
param keyVaultName string

// Parâmetros adicionais para BigQuery → Blob
param googleApplicationCredentials string // Caminho do JSON da service account

// =========================
// Módulos
// =========================

module logAnalytics './modules/loganalytics.bicep' = {
	name: 'logAnalytics'
	params: {
		location: location
		environment: environment
	}
}

module storage './modules/storage.bicep' = {
	name: 'storage'
	params: {
		location: location
		environment: environment
	}
}

module eventHub './modules/eventhub.bicep' = {
	name: 'eventHub'
	params: {
		location: location
		environment: environment
	}
}

module dataFactory './modules/datafactory.bicep' = {
	name: 'dataFactory'
	params: {
		location: location
		environment: environment
		dataFactoryName: dataFactoryName
	}
}

module bigqueryToBlob './modules/bigqueryToBlob.bicep' = {
	name: 'bigqueryToBlob'
	params: {
		dataFactoryName: dataFactoryName
		location: location
		storageAccountName: storageAccountName
		bronzeContainer: bronzeContainer
		googleApplicationCredentials: googleApplicationCredentials
	}
	dependsOn: [
		dataFactory
	]
}

module databricks './modules/databricks.bicep' = {
	name: 'databricks'
	params: {
		location: location
		environment: environment
	}
}

module keyVault './modules/keyvault.bicep' = {
	name: 'keyVault'
	params: {
		keyVaultName: keyVaultName
		location: location
		environment: environment
	}
}
