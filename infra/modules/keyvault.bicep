// =========================
// Azure Key Vault
// =========================

// Nome do Key Vault
param keyVaultName string

// Região de implantação
param location string

// Ambiente (dev, hml, prod)
param environment string = 'prod'

// =========================
// Key Vault
// =========================

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
	name: keyVaultName
	location: location

	tags: {
		Environment: environment
		Project: 'FIAP-TechChallenge'
	}

	properties: {
		tenantId: subscription().tenantId

		sku: {
			family: 'A'
			name: 'standard'
		}

		// RBAC pelo Azure AD
		enableRbacAuthorization: true

		// Permite acesso por serviços Azure
		enabledForDeployment: true
		enabledForTemplateDeployment: true
		enabledForDiskEncryption: true

		// Configuração de rede
		publicNetworkAccess: 'Enabled'

		networkAcls: {
			bypass: 'AzureServices'
			defaultAction: 'Allow'
		}

		softDeleteRetentionInDays: 90

		enableSoftDelete: true
	}
}

// =========================
// Outputs
// =========================

output keyVaultId string = kv.id
output keyVaultName string = kv.name
output keyVaultUri string = kv.properties.vaultUri
