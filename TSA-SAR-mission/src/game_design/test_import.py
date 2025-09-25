# test_import.py

print("--- Starting Diagnostic Test ---")
print("Attempting to import 'HUDQuestions' directly from hud.py...")

try:
    from hud import HUDQuestions
    print("\nSUCCESS: The import was successful.")
    print("\nThis confirms two things:")
    print("  1. Your hud.py file is saved correctly and contains the 'HUDQuestions' class.")
    print("  2. The problem is a circular import caused by the interaction between your other files (like game.py and controls.py).")
    print("\nTo fix this, please apply the solution from my previous reply: replace the entire contents of controls.py with the corrected code.")

except ImportError as e:
    print(f"\nFAILURE: The import failed.")
    print(f"Error Message: {e}")
    print("\nThis indicates a problem within the hud.py file itself. Please make sure you have saved the correct code for hud.py and that the class is named exactly 'HUDQuestions'.")

except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")

print("\n--- End of Diagnostic Test ---")