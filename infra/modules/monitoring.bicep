@description('Nome do projeto')
param projectName string

@description('Ambiente')
param environment string

@description('Região do Azure')
param location string = resourceGroup().location

var logAnalyticsName = toLower(
  substring(
    replace('${projectName}-${environment}-law', '-', ''),
    0,
    63
  )
)

var appInsightsName = toLower(
  substring(
    replace('${projectName}-${environment}-appi', '-', ''),
    0,
    63
  )
)

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location

  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }

  tags: {
    Project: projectName
    Environment: environment
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'

  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }

  tags: {
    Project: projectName
    Environment: environment
  }
}

output logAnalyticsWorkspaceName string = logAnalytics.name

output logAnalyticsWorkspaceId string = logAnalytics.id

output applicationInsightsName string = appInsights.name

output applicationInsightsConnectionString string = appInsights.properties.ConnectionString