'Hello, this is "M.H.A-V1.0.1", a simple mental health assistant.
'Created for anyone in reconstruction, following a burnout or other hard blow in life.
'Based on the principle that our doubts are over but that we can fall very low in our self-esteem during this short period,
'it is necessary to set up tools and new habits must be put in place quickly before locking oneself into a vegetative state.
'This is not the ideal tool but a trial under development.
'If you want to participate in its evolution, I invite you to create a commit, or share your ideas and advice with me in the comments. For to build a relevant tool together. Thanks
'To use the wizard please download it, then simply open it with a double click, the vbs format is supported by all windows computers.
'Currently working on a version developed with python and tkinter- by berru 22 "M.H.A-V1.0.1"


Dim x
'MsgBox(Message [, Button(s) + Icon + Button_selected_by_default] [, WindowTitle] )

x = msgbox("Are you feeling good today?",4+32+0,"Hello")
If x = 6 Then
        x = msgbox("Do you visualize your day?",4+64,"Very well preserve this inner peace")
        If x = 6 Then
                msgbox "Send a message of gratitude now if you feel it!",0+64,"Mantras"
                Else
                x = msgbox("Do you think your ego gets in the way of your understanding?",4+32,"Those thoughts don't belong to you")
If x = 6 Then
                        msgbox "Your mind isn't you! It's a law",0+48,"It's just the chemistry in your brain"
                        Else
                        msgbox "you're talking sh*t. Reason yourself. Believe in the future", 16,"Listen to your body and your heart"
                End If
        End If
Else
        x = msgbox("Breathe, be aware of the moment with your heart. Feeling better?",4+32,"These thoughts don't belong to you!")
        If x = 6 Then
                msgbox "Take 2 min to get inked",0+64,"Master your transient anxiety!"
                Else
                msgbox "Dissociate your mind from your brain! Take back control",0+64,"Stop what you're doing and meditate"
'end of V2
        End If
End If



'Preset
Dim Message, Bouton, Titre, Reponse, Resultat
Set objShell = CreateObject("Wscript.Shell")
'MsgBox "Ligne 1!!!" & Chr(10) & "Ligne 2!!!" & Chr(10) & "Ligne 3!!!"

Message = "On lance quel PRESET ?"	& Chr(10) & Chr(10)&"O = Work " & Chr(10)& Chr(10) & "N = Playlist" & Chr(10) & Chr(10) & "A = Quit"		'*** Message à afficher
Bouton = vbYesNoCancel + constante + vbDefaultButton1 	'définir les boutons et l'icône
Titre = "Programme Today"


Reponse = MsgBox(Message, Bouton, Titre)

If Reponse = "6" then
objShell.Run ("https://mail.google.com/mail")
objShell.Run ("https://calendar.google.com/calendar")

Elseif Reponse = "7" then
     objShell.Run ("https://www.youtube.com/playlist?list=PLl3AJf6HtsxVskm286G9o4ncUvH_4tVZw")

Else
     'msgBox "Belle journee "
    Wscript.Quit
End if