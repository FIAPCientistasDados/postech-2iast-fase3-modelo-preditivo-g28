// =========================
// Data Factory - BigQuery → Blob Bronze (via Databricks Notebook)
// =========================

param location string
param dataFactoryName string
param storageAccountName string
param bronzeContainer string

// Caminho do JSON da service account (no DBFS ou Secret Scope)
param googleApplicationCredentials string

// Lista de tabelas a exportar
@allowed([
  'basedosdados.br_inep_avaliacao_alfabetizacao.uf'
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil'
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf'
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio'
  'basedosdados.br_inep_avaliacao_alfabetizacao.municipio'
])
param tables array = [
  'basedosdados.br_inep_avaliacao_alfabetizacao.uf'
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil'
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf'
  'basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio'
  'basedosdados.br_inep_avaliacao_alfabetizacao.municipio'
]

// Linked Service para Databricks
resource databricksls 'Microsoft.DataFactory/factories/linkedservices@2018-06-01' = {
  name: '${dataFactoryName}/DatabricksLS'
  properties: {
    type: 'AzureDatabricks'
    typeProperties: {
      domain: 'https://adb-<seu-workspace-id>.azuredatabricks.net'
      accessToken: '<usar token do .ENV ou Key Vault>'
    }
  }
}

// Pipeline que chama o Notebook no Databricks
resource copyPipeline 'Microsoft.DataFactory/factories/pipelines@2018-06-01' = {
  name: '${dataFactoryName}/bigquerytoblobpipeline'
  properties: {
    activities: [
      {
        name: 'RunDatabricksNotebook'
        type: 'DatabricksNotebook'
        linkedServiceName: {
          referenceName: 'DatabricksLS'
          type: 'LinkedServiceReference'
        }
        typeProperties: {
          notebookPath: '/Repos/fiap-techchallenge/jobs/main.py'
          baseParameters: {
            GOOGLE_APPLICATION_CREDENTIALS: googleApplicationCredentials
            BRONZE_CONTAINER: bronzeContainer
            TABLES: join(tables, ',')
          }
        }
      }
    ]
  }
}

// Trigger diário às 02h UTC
resource dailyTrigger 'Microsoft.DataFactory/factories/triggers@2018-06-01' = {
  name: '${dataFactoryName}/DailyTrigger'
  properties: {
    type: 'ScheduleTrigger'
    pipelines: [
      { pipelineReference: { referenceName: 'bigquerytoblobpipeline', type: 'PipelineReference' } }
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
