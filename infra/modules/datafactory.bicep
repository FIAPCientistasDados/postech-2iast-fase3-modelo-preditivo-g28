param location string
param environment string
param dataFactoryName string


resource adf 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: 'adf-fiap-techchallenge'
  location: location
}