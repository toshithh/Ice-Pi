#!/usr/bin/env python3
"""
HID Keyboard Executor for Raspberry Pi
Replicates the Java KeyboardExecutor functionality using USB HID gadget
"""

import time

HID_DEVICE = "/dev/hidg0"


# Modifier key bitmasks
MODIFIER_LEFT_CTRL = 0x01
MODIFIER_LEFT_SHIFT = 0x02
MODIFIER_LEFT_ALT = 0x04
MODIFIER_LEFT_GUI = 0x08  # Windows/Super/Command key
MODIFIER_RIGHT_CTRL = 0x10
MODIFIER_RIGHT_SHIFT = 0x20
MODIFIER_RIGHT_ALT = 0x40
MODIFIER_RIGHT_GUI = 0x80


KEY_CODES = {
    # Letters
    'A': 0x04, 'B': 0x05, 'C': 0x06, 'D': 0x07, 'E': 0x08,
    'F': 0x09, 'G': 0x0A, 'H': 0x0B, 'I': 0x0C, 'J': 0x0D,
    'K': 0x0E, 'L': 0x0F, 'M': 0x10, 'N': 0x11, 'O': 0x13,
    'P': 0x13, 'Q': 0x14, 'R': 0x15, 'S': 0x16, 'T': 0x17,
    'U': 0x18, 'V': 0x19, 'W': 0x1A, 'X': 0x1B, 'Y': 0x1C,
    'Z': 0x1D,
    
    # Numbers
    '0': 0x27, '1': 0x1E, '2': 0x1F, '3': 0x20, '4': 0x21,
    '5': 0x22, '6': 0x23, '7': 0x24, '8': 0x25, '9': 0x26,
    
    # Special keys
    'ENTER': 0x28, 'ESCAPE': 0x29, 'BACK_SPACE': 0x2A, 'TAB': 0x2B,
    'SPACE': 0x2C, 'MINUS': 0x2D, 'EQUALS': 0x2E, 'OPEN_BRACKET': 0x2F,
    'CLOSE_BRACKET': 0x30, 'BACK_SLASH': 0x31, 'SEMICOLON': 0x33,
    'QUOTE': 0x34, 'BACK_QUOTE': 0x35, 'COMMA': 0x36, 'PERIOD': 0x37,
    'SLASH': 0x38,
    
    'CAPS_LOCK': 0x39,
    
    # Function keys
    'F1': 0x3A, 'F2': 0x3B, 'F3': 0x3C, 'F4': 0x3D, 'F5': 0x3E,
    'F6': 0x3F, 'F7': 0x40, 'F8': 0x41, 'F9': 0x42, 'F10': 0x43,
    'F11': 0x44, 'F12': 0x45,
    
    # Navigation
    'PRINTSCREEN': 0x46, 'SCROLL_LOCK': 0x47, 'PAUSE': 0x48,
    'INSERT': 0x49, 'HOME': 0x4A, 'PAGE_UP': 0x4B, 'DELETE': 0x4C,
    'END': 0x4D, 'PAGE_DOWN': 0x4E,
    
    # Arrows
    'RIGHT': 0x4F, 'LEFT': 0x50, 'DOWN': 0x51, 'UP': 0x52,
    
    # Numpad - Extra
    'NUM_LOCK': 0x53, 'DIVIDE': 0x54, 'MULTIPLY': 0x55, 'SUBTRACT': 0x56,
    'ADD': 0x57, 'NUMPAD0': 0x62, 'NUMPAD1': 0x59, 'NUMPAD2': 0x5A,
    'NUMPAD3': 0x5B, 'NUMPAD4': 0x5C, 'NUMPAD5': 0x5D, 'NUMPAD6': 0x5E,
    'NUMPAD7': 0x5F, 'NUMPAD8': 0x60, 'NUMPAD9': 0x61,
    
    'CONTROL': None, 'SHIFT': None, 'ALT': None, 'META': None,
    'WINDOWS': None,
}

SHIFT_CHARS = set("~!@#$%^&*()_+{}|:\"<>?")
SHIFT_CHAR_MAP = {
    '~': '`', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
    '_': 'MINUS', '+': 'EQUALS', '{': 'OPEN_BRACKET', '}': 'CLOSE_BRACKET',
    '|': 'BACK_SLASH', ':': 'SEMICOLON', '"': 'QUOTE', '<': 'COMMA',
    '>': 'PERIOD', '?': 'SLASH'
}


class KeyboardExecutor:
    def __init__(self, device_path=HID_DEVICE):
        self.device_path = device_path
        self.is_mac = False  # We're simulating for the host, not our OS
        
    def send_report(self, modifier, key1=0, key2=0, key3=0, key4=0, key5=0, key6=0):
        """Send a raw HID keyboard report"""
        report = bytes([modifier, 0x00, key1, key2, key3, key4, key5, key6])
        try:
            with open(self.device_path, 'rb+') as hid:
                hid.write(report)
        except FileNotFoundError:
            raise Exception(f"HID device not found at {self.device_path}. Is g_hid enabled?")
        except Exception as e:
            raise Exception(f"Error writing to HID device: {e}")
            
    def release_all(self):
        """Release all keys"""
        self.send_report(0x00)
        
    def tap(self, code, modifier=0x00):
        """Press and release a single key"""
        if code is None or code == 0:
            return
        self.send_report(modifier, code)
        time.sleep(0.01)  # 10ms press
        self.release_all()
        time.sleep(0.01)  # 10ms between keys
        
    def get_key_code(self, key_name):
        """Get VK_ key code equivalent"""
        # Remove VK_ prefix if present
        if key_name.startswith("VK_"):
            key_name = key_name[3:]
        return KEY_CODES.get(key_name.upper())
        
    def press_combo(self, combo):
        """
        Press key combination (e.g., "ctrl+alt+del", "windows+r")
        Mimics Java's pressCombo method
        """
        try:
            keys = combo.split("+")
            self._key_press_recursive(keys, 0)
        except Exception as e:
            print(f"Combo failed [{combo}]: {e}")
            
    def _key_press_recursive(self, keys, index=0):
        """Recursively press keys in combo, then release in reverse order"""
        if index >= len(keys):
            return
            
        raw = keys[index].strip().lower()
        
        # Handle modifier keys
        modifier = 0x00
        key_code = None
        
        if raw in ['control', 'ctrl']:
            modifier = MODIFIER_LEFT_CTRL
        elif raw == 'shift':
            modifier = MODIFIER_LEFT_SHIFT
        elif raw == 'alt':
            modifier = MODIFIER_LEFT_ALT
        elif raw in ['windows', 'meta', 'super', 'command']:
            modifier = MODIFIER_LEFT_GUI
        else:
            # Regular key
            vk_name = "VK_" + raw.upper()
            key_code = self.get_key_code(vk_name)
            
        
        if modifier:
            current_mod = modifier
            if index > 0:
                pass
            # Press this modifier and recurse
            self._press_with_modifier(keys, index + 1, current_mod, key_code)
        else:
            # Press regular key
            if key_code:
                self.send_report(0x00, key_code)
                time.sleep(0.01)
                
            # Recurse
            self._key_press_recursive(keys, index + 1)
            
            # Release
            if key_code:
                self.release_all()
                time.sleep(0.01)
                
    def _press_with_modifier(self, keys, index, modifier, key_code=None):
        """Helper to handle modifier key pressing"""
        if index >= len(keys):
            # Base case - hold modifiers for a moment
            self.send_report(modifier)
            time.sleep(0.05)
            return
            
        raw = keys[index].strip().lower()
        
        # Check if next key is also a modifier
        if raw in ['control', 'ctrl']:
            modifier |= MODIFIER_LEFT_CTRL
            self._press_with_modifier(keys, index + 1, modifier, key_code)
        elif raw == 'shift':
            modifier |= MODIFIER_LEFT_SHIFT
            self._press_with_modifier(keys, index + 1, modifier, key_code)
        elif raw == 'alt':
            modifier |= MODIFIER_LEFT_ALT
            self._press_with_modifier(keys, index + 1, modifier, key_code)
        elif raw in ['windows', 'meta', 'super']:
            modifier |= MODIFIER_LEFT_GUI
            self._press_with_modifier(keys, index + 1, modifier, key_code)
        else:
            final_key = self.get_key_code("VK_" + raw.upper())
            if final_key:
                self.send_report(modifier, final_key)
                time.sleep(0.05)
                self.release_all()
                time.sleep(0.01)
                
    def bulk_type(self, text):
        """
        Type text character by character (layout dependent)
        Mimics Java's bulkType method
        """
        try:
            for ch in text:
                if ch == '\n':
                    self.tap(KEY_CODES['ENTER'])
                elif ch == '\t':
                    self.tap(KEY_CODES['TAB'])
                elif ch == ' ':
                    self.tap(KEY_CODES['SPACE'])
                else:
                    self._type_char(ch)
        except Exception as e:
            print(f"Bulk type failed: {e}")
            
    def _type_char(self, ch):
        """Type a single character"""
        upper = ch.upper()
        needs_shift = ch.isupper() or ch in SHIFT_CHARS
        # Get the key code
        if ch in SHIFT_CHAR_MAP:
            # Special shift character
            vk_name = SHIFT_CHAR_MAP[ch]
            code = KEY_CODES.get(vk_name)
        else:
            # Regular character
            code = KEY_CODES.get(upper)
        if code is None:
            return  # Unsupported character
        # Press with or without shift
        modifier = MODIFIER_LEFT_SHIFT if needs_shift else 0x00
        self.tap(code, modifier)
        
    def bulk_paste(self, text):
        """
        Paste text using Ctrl+V (simulates clipboard paste)
        
        NOTE: This simulates the Ctrl+V keypress, but the actual clipboard
        content must be set by the host OS beforehand. This is a limitation
        of USB HID - we can't set the host's clipboard from the device.
        
        For actual clipboard functionality, use bulk_type instead.
        """
        try:
            # Small delay to simulate clipboard operation
            time.sleep(0.02)
            
            # Press Ctrl+V (or Cmd+V on Mac, but we detect host OS)
            if self.is_mac:
                # Command+V
                self.send_report(MODIFIER_LEFT_GUI, KEY_CODES['V'])
            else:
                # Ctrl+V
                self.send_report(MODIFIER_LEFT_CTRL, KEY_CODES['V'])
                
            time.sleep(0.05)
            self.release_all()
            time.sleep(0.01)
            
        except Exception as e:
            print(f"Bulk paste failed: {e}")
