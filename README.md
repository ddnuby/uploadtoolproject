This is a an upload and download tool for the database. The tool uploads the excel file into the database with several functions present (override, merge, and create), as well as can download the tables converted into an excel file

Choose Template page: This page is for choosing a template, such as Testing Excel First, and all of those templates have different functions that happen prior to the uploading the Excel file into the database. 
  Each template is fetched from a table in the main database, called template. It has a corresponding function (override, create or merge) as well as a foreign id (this is the way the connection string is fetched from another table according to the template selected), and a table name(s) that are present in the such database.
  The override function truncates the table according to the template in the database and rewrites it with the new data from the excel file that is being uploaded into that database
  The merge function merges the new data from the Excel file with the existing data in the template (database) selected
  THe create function creates a table (if it already does not exist) in the template (database) selecte
Choose Regclass page is stil being implemented
Download Page is for searching for a table to download. It converts the chosen table into an excel file with the Excel file's name being the template name and the worksheet(s) name(s) being the table name(s) from the database. 

