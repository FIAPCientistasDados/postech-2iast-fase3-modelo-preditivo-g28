// =========================
// Data Factory - Pipeline Python via Databricks
// =========================

param location string
param dataFactoryName string
param databricksHost string
param databricksToken string
param sparkJob string
param googleApplicationCredentials string
param bronzeContainer string

// Linked Service para Databricks
resource databricksls 'Microsoft.DataFactory/factories/linkedservices@2018-06-01' = {
  name: '${dataFactoryName}/DatabricksLS'
  properties: {
    type: 'AzureDatabricks'
    typeProperties: {
      domain: databricksHost
      accessToken: databricksToken
    }
  }
}

// Pipeline que executa o script Python no Databricks
resource pythonPipeline 'Microsoft.DataFactory/factories/pipelines@2018-06-01' = {
  name: '${dataFactoryName}/BigQueryPythonPipeline'
  properties: {
    activities: [
      {
        name: 'RunPythonBigQueryExport'
        type: 'DatabricksNotebook'
        linkedServiceName: {
          referenceName: 'DatabricksLS'
          type: 'LinkedServiceReference'
        }
        typeProperties: {
          notebookPath: sparkJob
          baseParameters: {
            GOOGLE_APPLICATION_CREDENTIALS: googleApplicationCredentials
            BRONZE_CONTAINER: bronzeContainer
          }
        }
      }
    ]
  }
}

// Trigger diário às 02h UTC
resource dailyTrigger 'Microsoft.DataFactory/factories/triggers@2018-06-01' = {
  name: '${dataFactoryName}/DailyTriggerPython'
  properties: {
    type: 'ScheduleTrigger'
    pipelines: [
      {
        pipelineReference: {
          referenceName: 'BigQueryPythonPipeline'
          type: 'PipelineReference'
        }
      }
    ]
    typeProperties: {
      recurrence: {
        frequency: 'Day'
        interval: 1
        startTime: '2026-08-22T02:00:00Z'
        timeZone: 'UTC'
      }
    }
  }
}
