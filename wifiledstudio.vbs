
' ----- ExeScript Options Begin -----
' ScriptType: window
' DestDirectory: temp
' Icon: none
' OutputFile: C:\Users\tuant\Desktop\321.exe
' ----- ExeScript Options End -----
KillProc "ambilightwifid.exe"

Sub KillProc( myProcess )
'Authors: Denis St-Pierre and Rob van der Woude
'Purpose: Kills a process and waits until it is truly dead

    Dim blnRunning, colProcesses, objProcess
    blnRunning = False

    Set colProcesses = GetObject( _
                       "winmgmts:{impersonationLevel=impersonate}" _
                       ).ExecQuery( "Select * From Win32_Process" )
    For Each objProcess in colProcesses
        If LCase( myProcess ) = LCase( objProcess.Name ) Then
            ' Confirm that the process was actually running
            blnRunning = True
            ' Get exact case for the actual process name
            myProcess  = objProcess.Name
            ' Kill all instances of the process
            objProcess.Terminate()
        End If
    Next

    If blnRunning Then
        ' Wait and make sure the process is terminated.
        ' Routine written by Denis St-Pierre.
        Do Until Not blnRunning
            Set colProcesses = GetObject( _
                               "winmgmts:{impersonationLevel=impersonate}" _
                               ).ExecQuery( "Select * From Win32_Process Where Name = '" _
                             & myProcess & "'" )
            WScript.Sleep 100 'Wait for 100 MilliSeconds
            If colProcesses.Count = 0 Then 'If no more processes are running, exit loop
                blnRunning = False
            End If
		Loop
    End If
End Sub

KillProc "MultiAmbilightWiFi.exe"

Sub KillProc( myProcess )
'Authors: Denis St-Pierre and Rob van der Woude
'Purpose: Kills a process and waits until it is truly dead

    Dim blnRunning, colProcesses, objProcess
    blnRunning = False

    Set colProcesses = GetObject( _
                       "winmgmts:{impersonationLevel=impersonate}" _
                       ).ExecQuery( "Select * From Win32_Process" )
    For Each objProcess in colProcesses
        If LCase( myProcess ) = LCase( objProcess.Name ) Then
            ' Confirm that the process was actually running
            blnRunning = True
            ' Get exact case for the actual process name
            myProcess  = objProcess.Name
            ' Kill all instances of the process
            objProcess.Terminate()
        End If
    Next

    If blnRunning Then
        ' Wait and make sure the process is terminated.
        ' Routine written by Denis St-Pierre.
        Do Until Not blnRunning
            Set colProcesses = GetObject( _
                               "winmgmts:{impersonationLevel=impersonate}" _
                               ).ExecQuery( "Select * From Win32_Process Where Name = '" _
                             & myProcess & "'" )
            WScript.Sleep 100 'Wait for 100 MilliSeconds
            If colProcesses.Count = 0 Then 'If no more processes are running, exit loop
                blnRunning = False
            End If
		Loop
    End If
End Sub

KillProc "WiFi Led Studio.exe"

Sub KillProc( myProcess )
'Authors: Denis St-Pierre and Rob van der Woude
'Purpose: Kills a process and waits until it is truly dead

    Dim blnRunning, colProcesses, objProcess
    blnRunning = False

    Set colProcesses = GetObject( _
                       "winmgmts:{impersonationLevel=impersonate}" _
                       ).ExecQuery( "Select * From Win32_Process" )
    For Each objProcess in colProcesses
        If LCase( myProcess ) = LCase( objProcess.Name ) Then
            ' Confirm that the process was actually running
            blnRunning = True
            ' Get exact case for the actual process name
            myProcess  = objProcess.Name
            ' Kill all instances of the process
            objProcess.Terminate()
        End If
    Next

    If blnRunning Then
        ' Wait and make sure the process is terminated.
        ' Routine written by Denis St-Pierre.
        Do Until Not blnRunning
            Set colProcesses = GetObject( _
                               "winmgmts:{impersonationLevel=impersonate}" _
                               ).ExecQuery( "Select * From Win32_Process Where Name = '" _
                             & myProcess & "'" )
            WScript.Sleep 100 'Wait for 100 MilliSeconds
            If colProcesses.Count = 0 Then 'If no more processes are running, exit loop
                blnRunning = False
            End If
		Loop
    End If
End Sub

Dim objShell, targetpath, strAttr
Set objShell = WScript.CreateObject( "WScript.Shell" )
targetpath = objShell.ExpandEnvironmentStrings("""%ProgramFiles%\WiFi Led Studio\WiFi Led Studio.exe""")
strAttr = " --open-ui"
objShell.Run targetpath & strAttr
'Set objShell = Nothing