Import-Module sqlserver



# Connection parameters:

$sqlInstance = ".\SQL2019"
$databaseName = "SQLSaturday"

# Refresh the XML files?
# git pull




# Empty out the XML blob table:

Invoke-Sqlcmd `
    -Query "TRUNCATE TABLE [Raw].XML_Files;" `
    -ServerInstance $sqlInstance `
    -Database $databaseName `
    -OutputSqlErrors $true



# Stage everything into the database:

Get-ChildItem -Path "../raw/xml/SQLSat*.xml" | ForEach-Object {

    $xml = Get-Content $_.FullName -Raw -Encoding UTF8

    # I feel a little dirty for manually sanitizing my inputs, rather than
    # properly parameterizing the query, but here we go.
    $sql = "INSERT INTO [Raw].XML_Files ([Filename], Blob) " + `
           "VALUES ('" + $_.Name.replace("'", "''") + "', N'" + $xml.replace("'", "''") + "');"

    Invoke-Sqlcmd `
        -Query $sql `
        -ServerInstance $sqlInstance `
        -Database $databaseName `
        -OutputSqlErrors $true

}

