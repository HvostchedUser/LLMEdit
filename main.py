import threading
from time import sleep
from llama_cpp import Llama
import tkinter as tk
from tkinter import scrolledtext
import random
import colorsys


def generate_pastel_color(text):
    # Hash the input text to ensure reproducible colors for the same text
    hash_value = hash(text.encode())
    random.seed(hash_value)

    # Generate a random hue from 0 to 360
    hue = random.uniform(0, 360)
    # Set saturation to a low value for the pastel effect (10% to 30%)
    saturation = random.uniform(0.2, 0.4)
    # Set value to a high value to keep the color light (70% to 100%)
    value = random.uniform(0.7, 1.0)

    # Convert hue from 0-360 to 0-1 for colorsys compatibility
    hue_normalized = hue / 360.0

    # Convert HSV to RGB using colorsys
    r, g, b = colorsys.hsv_to_rgb(hue_normalized, saturation, value)

    # Convert RGB from 0-1 to 0-255 and then to hexadecimal
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'


def find_common_substrings(text1, text2):
    words1 = text1.split()
    words2 = text2.split()


    common_substrings = []
    len1, len2 = len(words1), len(words2)

    for i in range(len1):
        for j in range(len2):
            temp = []
            while i < len1 and j < len2 and words1[i] == words2[j]:
                temp.append(words1[i])
                i += 1
                j += 1

            if len(temp) > 1:
                common_substrings.append(' '.join(temp))

    return list(set(common_substrings))  # Remove duplicates


def highlight_text_in_editor(start, end, color="#FFD580"):
    """
    Highlights the specified range of text in the text editor.

    Args:
    start (str): The starting position of the text to highlight.
    end (str): The ending position of the text to highlight.
    color (str): The color to use for highlighting.
    """
    text_editor.tag_add(f"highlight-{color}", start, end)
    text_editor.tag_configure(f"highlight-{color}", background=color)


def clear_highlight_text_in_editor():
    for tag in text_editor.tag_names():
        text_editor.tag_delete(tag)


def clear_highlight_text_in_comments():
    for tag in ai_comments_text.tag_names():
        ai_comments_text.tag_delete(tag)


def highlight_text_in_comments(start, end, color="#FFD580"):
    """
    Highlights the specified range of text in the AI comments.

    Args:
    start (str): The starting position of the text to highlight.
    end (str): The ending position of the text to highlight.
    color (str): The color to use for highlighting.
    """
    ai_comments_text.tag_add(f"highlight-{color}", start, end)
    ai_comments_text.tag_configure(f"highlight-{color}", background=color)


def get_current_text():
    """
    Returns the current text in the text editor.

    Returns:
    str: The current text in the editor.
    """
    return text_editor.get("1.0", tk.END)


def get_system_prompt():
    """
    Returns the current text in the text editor.

    Returns:
    str: The current text in the editor.
    """
    return ai_instructions_text.get("1.0", tk.END)


def set_ai_comments(comments):
    """
    Sets the AI comments in the AI panel.

    Args:
    comments (str): The comments to display in the AI panel.
    """
    ai_comments_text.configure(state=tk.NORMAL)
    ai_comments_text.delete("1.0", tk.END)
    ai_comments_text.insert(tk.END, comments)
    ai_comments_text.see(tk.END)  # Auto-scroll to the bottom
    ai_comments_text.configure(state=tk.DISABLED)


def append_ai_comments(comments):
    """
    Appends to the AI comments in the AI panel.

    Args:
    comments (str): The comments to append in the AI panel.
    """
    ai_comments_text.configure(state=tk.NORMAL)
    ai_comments_text.insert(tk.END, comments)
    ai_comments_text.see(tk.END)  # Auto-scroll to the bottom
    ai_comments_text.configure(state=tk.DISABLED)


def highlight_processing(editor_text, ai_text):
    clear_highlight_text_in_editor()
    clear_highlight_text_in_comments()

    common_subs = find_common_substrings(editor_text, ai_text)
    common_subs.sort(key=len)
    for sub in common_subs:
        color = generate_pastel_color(sub)
        start_idx_editor = editor_text.find(sub)
        start_idx_ai = ai_text.find(sub)

        if start_idx_editor != -1:
            start_pos_editor = f'1.0+{start_idx_editor} chars'
            end_pos_editor = f'1.0+{start_idx_editor + len(sub)} chars'
            highlight_text_in_editor(start_pos_editor, end_pos_editor, color)

        if start_idx_ai != -1:
            start_pos_ai = f'1.0+{start_idx_ai} chars'
            end_pos_ai = f'1.0+{start_idx_ai + len(sub)} chars'
            highlight_text_in_comments(start_pos_ai, end_pos_ai, color)


def start_ai_processing():
    """
    Initiates AI processing.
    """
    global ai_processing_active, ai_processing_generation
    while ai_processing_generation:
        ai_processing_active = False
        sleep(0.1)
    ai_processing_active = True
    ai_comments_label.config(text="AI is reading... ")
    system_prompt = get_system_prompt()
    current_text = get_current_text()
    # Construct the prompt for the LLM
    prompt = f"{turn_system}You are an AI text editor. Your task: \n{system_prompt}{turn_user}Here is the text: \n{current_text}{turn_assistant}"
    ai_processing_generation = True
    generator = llm(
        prompt,
        max_tokens=2048,
        stop=["<|im_end|>"],
        stream=True,
        temperature=0.2,
        top_p=0.9,
        repeat_penalty=1.15,
        top_k=20,
    )
    set_ai_comments("")
    full_str = ""
    iter = 0
    for output in generator:
        if iter == 0:
            ai_comments_label.config(text="AI is writing... ")
        iter += 1
        if not ai_processing_active:
            ai_processing_generation = False
            ai_comments_label.config(text="AI Comments: ")
            return
        token_str = output["choices"][0]["text"]
        full_str += token_str
        if not ai_processing_active:
            return
        append_ai_comments(token_str)
        if iter%20==0:
            highlight_processing(current_text, full_str)

    ai_comments_label.config(text="AI Comments: ")

    set_ai_comments(full_str)
    highlight_processing(current_text, full_str)

    ai_processing_generation = False


def on_text_change(event):
    """
    Event handler for text changes in the text editor. Resets the AI processing timer.

    Args:
    event: The event object.
    """
    global ai_processing_timer, ai_processing_active, sum_text_hash
    new_hash = hash((get_current_text() + get_system_prompt()))
    if sum_text_hash == new_hash:
        return

    sum_text_hash = new_hash
    if ai_processing_timer:
        ai_processing_timer.cancel()
    ai_processing_active = False  # Reset the flag to stop ongoing AI processing

    ai_processing_timer = threading.Timer(1.0, start_ai_processing)
    ai_processing_timer.start()


def on_text_select_all(event):
    """
    Selects all text in the widget that triggered the event.

    Args:
    event: The event object.
    """
    event.widget.tag_add(tk.SEL, "1.0", tk.END)
    return "break"


# Large Language Model Initialisation
llm = Llama(
    model_path="dolphin-2_6-phi-2.Q4_K_M.gguf",
    verbose=False,
    n_ctx=2048
)
turn_system = "<|im_start|>system\n"
turn_user = "<|im_end|>\n<|im_start|>user\n"
turn_assistant = "<|im_end|>\n<|im_start|>assistant\n"

# Initialize the main window
root = tk.Tk()
root.title("llmedit")
root.configure(bg="#F0F0F0")

# Create frames for the text editing pane and the AI panel
editor_frame = tk.Frame(root, bg="#F0F0F0")
ai_frame = tk.Frame(root, bg="#F0F0F0", width=200)

editor_frame.pack(side="left", fill="both", expand=True)
ai_frame.pack(side="right", fill="y")

# Create the text editing pane with line numbers
text_editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.WORD, undo=True, borderwidth=0)
text_editor.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
text_editor.bind("<Control-a>", on_text_select_all)
text_editor.bind("<KeyRelease>", on_text_change)

# Initialize the timer variable and the processing active flag
ai_processing_timer = None
ai_processing_active = False
ai_processing_generation = False

# Bind the text change event in the text_editor widget
text_editor.bind("<KeyRelease>", on_text_change)

# On text change helper value
sum_text_hash = 0

# Create components for the AI panel
ai_instructions_label = tk.Label(ai_frame, text="Instructions:", bg="#F0F0F0")
ai_instructions_label.pack(pady=(10, 5))
ai_instructions_text = scrolledtext.ScrolledText(ai_frame, wrap=tk.WORD, height=5, borderwidth=0, undo=True)
ai_instructions_text.pack(pady=5, fill=tk.X, padx=10)
ai_instructions_text.bind("<Control-a>", on_text_select_all)
ai_instructions_text.bind("<KeyRelease>", on_text_change)

ai_comments_label = tk.Label(ai_frame, text="AI comments: ", bg="#F0F0F0")
ai_comments_label.pack(pady=(10, 5))
ai_comments_text = scrolledtext.ScrolledText(ai_frame, wrap=tk.WORD, height=10, borderwidth=0, state=tk.DISABLED)
ai_comments_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
ai_comments_text.bind("<Control-a>", on_text_select_all)

# Apply flat design to scrollbars
for widget in [text_editor, ai_instructions_text, ai_comments_text]:
    for scrollbar in [widget.vbar]:
        scrollbar.config(troughcolor="#F0F0F0", borderwidth=0)

# Define font settings
default_font = ("Arial", 16)  # You can adjust the size here
text_editor.configure(font=default_font)
ai_instructions_text.configure(font=default_font)
ai_comments_text.configure(font=default_font)

# Start the Tkinter event loop
root.mainloop()
