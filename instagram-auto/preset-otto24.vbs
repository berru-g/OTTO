Dim preset_du_jour
preset_du_jour = MsgBox("Otto:" & vbCrLf & "1. Set up" & vbCrLf & "2. optimisation" & vbCrLf & "3. Insta otto", vbQuestion + vbYesNoCancel, "preset_du_jour")

If preset_du_jour = vbYes Then
    ' Ouvrir un fichier, une page web et une application
    Dim fichier, pageWeb, application
    fichier = "C:\Chemin\Vers\Votre\Fichier.txt"
    pageWeb = "https://www.votrepageweb.com"
    application = "C:\Chemin\Vers\Votre\Application.exe"

    Set objShell = CreateObject("WScript.Shell")
    objShell.Run fichier
    objShell.Run "cmd /c start " & pageWeb
    objShell.Run application
ElseIf preset_du_jour = vbNo Then
    ' Afficher les tâches en cours
    Set objShell = CreateObject("WScript.Shell")
    objShell.Run "cmd /c netstat -ano"', 1, True
	WScript.Sleep 10000
    ' Vérification des tâches inutiles - à faire manuellement ou avec un script externe plus complexe
ElseIf preset_du_jour = vbCancel Then
    ' Ouvrir un site en navigation privée et entrer les informations d'identification
    Dim navigateur, url, identifiant, motDePasse
    navigateur = "firefox.exe" ' ou "firefox.exe" selon votre navigateur
    url = "https://www.instagram.com"
    identifiant = "id"
    motDePasse = "mdp"

    Set objShell = CreateObject("WScript.Shell")
    objShell.Run "firefox.exe -private-window " '& url
    WScript.Sleep 2000 ' Attendre que le navigateur s'ouvre
	
    ' Automatiser la saisie du login et du mot de passe - peut nécessiter un outil comme AutoIt pour une solution robuste
    objShell.SendKeys url
	objShell.SendKeys "{ENTER}"
	WScript.Sleep 4000
	'"Refuser les cookies"
	objShell.SendKeys "{TAB 15}"  
	objShell.SendKeys "{ENTER}"
	WScript.Sleep 3000
    'login
	objShell.SendKeys "{TAB 2}"
	objShell.SendKeys identifiant
    objShell.SendKeys "{TAB}"
    objShell.SendKeys motDePasse
    objShell.SendKeys "{ENTER}"
	WScript.Sleep 7000
	'publication
	objShell.SendKeys "{TAB 8}"
    objShell.SendKeys "{ENTER}"
	WScript.Sleep 2000
	objShell.SendKeys "{TAB}"
    objShell.SendKeys "{ENTER}"
	'scroll et like auto
	'Set objShell = CreateObject("WScript.Shell")
    'objShell.Run "./otto.py"
	
End If
