param location string
param environment string

resource databricks 'Microsoft.Databricks/workspaces@2023-02-01' = {
  name: 'dbw-fiap-techchallenge-${environment}'
  location: location

  sku: {
    name: 'premium'
  }

  properties: {
    managedResourceGroupId: '/subscriptions/${subscription().subscriptionId}/resourceGroups/rg-managed-databricks-${environment}'
  }
}
