### Attention, cette app est à but éducative 

    - Il s'agit d'un keylogger, cela représente un danger si vous la telechargez donc ne le faite pas !
    - Cette app sera hebergé le temps que je finisse de démontrer à un ami comment ça marche et comment s'en proteger. Elle sera effacé de mon github. 

#### Step :

    - .py to script .exe

    pip install pyinstaller
    pyinstaller --onefile tonscript.py

    - .exe to .apk for android
    pip install kivy buildozer
    # buildozer init
    # buildozer android debug