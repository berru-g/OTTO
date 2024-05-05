' Flemme corporation, tout ce qui nous fait gagner deux minutes est bon à prendre.
' Automatisation de la creation dun dossier front avec fichier, HTML, CSS, JS et readme.md
Dim fso, folder, indexFile, styleFile, scriptFile, shell, folderPath

' Créer une instance de FileSystemObject
Set fso = CreateObject("Scripting.FileSystemObject")

' Chemin du dossier "new project" dans le dossier "Documents"
folderPath = fso.BuildPath(WScript.CreateObject("WScript.Shell").SpecialFolders("MyDocuments"), "new project")

' Vérifier si le dossier existe déjà, sinon le créer
If Not fso.FolderExists(folderPath) Then
    Set folder = fso.CreateFolder(folderPath)
End If

' Créer les fichiers index.html, style.css et script.js dans le dossier
Set indexFile = fso.CreateTextFile(fso.BuildPath(folderPath, "index.html"), True)
indexFile.WriteLine("<!DOCTYPE html>")
indexFile.WriteLine("<!--otto by berru-g/github.com-->")
indexFile.WriteLine("<html>")
indexFile.WriteLine("<head>")
indexFile.WriteLine("  <title>My New Project</title>")
' indexFile.WriteLine("  <meta charset="UTF-8">")
' indexFile.WriteLine("  <meta name="viewport" content="width=device-width, initial-scale=1">")
' indexFile.WriteLine("  <meta name="keywords" content="">")
' indexFile.WriteLine(" <meta name="description" content=""")
indexFile.WriteLine("</head>")
indexFile.WriteLine("<body>")
indexFile.WriteLine("  <h1>Hello, world!</h1>")
indexFile.WriteLine("  <p>sub-title</p>")
indexFile.WriteLine("</body>")
indexFile.WriteLine("</html>")
indexFile.Close

Set styleFile = fso.CreateTextFile(fso.BuildPath(folderPath, "style.css"), True)
styleFile.WriteLine("/* CSS styles */")
styleFile.WriteLine("body {")
styleFile.WriteLine("  background-color: #f0f0f0;")
styleFile.WriteLine("  margin: 0;")
styleFile.WriteLine("  padding: 0 0;")
styleFile.WriteLine("}")
styleFile.WriteLine("h1 {")
styleFile.WriteLine("  color: #00f;")
styleFile.WriteLine("}")
styleFile.Close

Set scriptFile = fso.CreateTextFile(fso.BuildPath(folderPath, "script.js"), True)
scriptFile.WriteLine("// JavaScript code")
scriptFile.WriteLine("document.addEventListener('DOMContentLoaded', function() {")
scriptFile.WriteLine("  console.log('Hello, world!');")
scriptFile.WriteLine("});")
scriptFile.Close

Set scriptFile = fso.CreateTextFile(fso.BuildPath(folderPath, "readme.md"), True)
scriptFile.WriteLine("# title")
scriptFile.WriteLine("## subtitle")
scriptFile.Close

' Ouvrir le dossier du nouveau projet dans VSCode
' C:\Users\your_user_name\Documents\new project
Set shell = CreateObject("WScript.Shell")
shell.Run "code ." & folderPath
' Ouvrir le dossier du nouveau projet dans l'explorateur de fichiers
Set shell = CreateObject("Shell.Application")
shell.Open folderPath
