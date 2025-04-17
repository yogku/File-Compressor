import heapq
import os
import pickle
from tkinter import filedialog, messagebox, Tk, Button, Label, Text, Scrollbar, Frame, BOTH, RIGHT, Y, END
from collections import defaultdict

# ---------------- Huffman Coding Core ----------------

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_dict(text):
    freq = defaultdict(int)
    for char in text:
        freq[char] += 1
    return freq

def build_huffman_tree(freq_dict):
    heap = [Node(char, freq) for char, freq in freq_dict.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        merged = Node(None, node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2
        heapq.heappush(heap, merged)

    return heap[0]

def generate_codes(root):
    codes = {}
    def helper(node, current_code):
        if node is None:
            return
        if node.char is not None:
            codes[node.char] = current_code
            return
        helper(node.left, current_code + "0")
        helper(node.right, current_code + "1")
    helper(root, "")
    return codes

def compress_text(text, codes):
    return ''.join(codes[char] for char in text)

def pad_encoded_text(encoded_text):
    extra_padding = 8 - len(encoded_text) % 8
    padded_info = f"{extra_padding:08b}"
    encoded_text += "0" * extra_padding
    return padded_info + encoded_text

def get_byte_array(padded_encoded_text):
    return bytearray(int(padded_encoded_text[i:i+8], 2) for i in range(0, len(padded_encoded_text), 8))

def compress_file(input_file, output_file):
    with open(input_file, 'r') as f:
        text = f.read()

    freq_dict = build_frequency_dict(text)
    huffman_tree = build_huffman_tree(freq_dict)
    codes = generate_codes(huffman_tree)
    encoded_text = compress_text(text, codes)
    padded_encoded_text = pad_encoded_text(encoded_text)
    byte_array = get_byte_array(padded_encoded_text)

    with open(output_file, 'wb') as out:
        out.write(bytes(byte_array))

    # Save code mapping
    with open(output_file + ".codes", 'wb') as f:
        pickle.dump(codes, f)

    original_size = os.path.getsize(input_file) / 1024
    compressed_size = os.path.getsize(output_file) / 1024

    return codes, output_file, original_size, compressed_size

# ---------------- Decompression  ----------------

def remove_padding(padded_encoded_text):
    extra_padding = int(padded_encoded_text[:8], 2)
    encoded_text = padded_encoded_text[8:]  
    return encoded_text[:-extra_padding]  

def decode_text(encoded_text, codes):
    reverse_codes = {v: k for k, v in codes.items()}
    current_code = ""
    decoded_text = ""
    for bit in encoded_text:
        current_code += bit
        if current_code in reverse_codes:
            decoded_text += reverse_codes[current_code]
            current_code = ""
    return decoded_text

def decompress_file(compressed_file, output_file):
    with open(compressed_file, 'rb') as f:
        bit_string = ''.join(f"{byte:08b}" for byte in f.read())

    with open(compressed_file + ".codes", 'rb') as f:
        codes = pickle.load(f)

    encoded_text = remove_padding(bit_string)
    decompressed_text = decode_text(encoded_text, codes)

    with open(output_file, 'w') as out:
        out.write(decompressed_text)

    return output_file

# ---------------- Tkinter GUI ----------------

def select_file():
    input_path = filedialog.askopenfilename(title="Select text file", filetypes=[("Text files", "*.txt")])
    if input_path:
        output_path = os.path.splitext(input_path)[0] + "_compressed.bin"
        try:
            codes, output_file, original_size, compressed_size = compress_file(input_path, output_path)

            status = (
                f"✅ Compression Complete\n\n"
                f"📄 Original File: {round(original_size, 2)} KB\n"
                f"📦 Compressed File: {round(compressed_size, 2)} KB\n"
                f"🗂 Saved at: {output_file}"
            )
            status_label.config(text=status)

            code_display.delete("1.0", END)
            for char, code in codes.items():
                line = f"{repr(char)} : {code}\n"
                code_display.insert(END, line)

        except Exception as e:
            messagebox.showerror("Error", str(e))

def select_file_to_decompress():
    input_path = filedialog.askopenfilename(title="Select .bin File", filetypes=[("Binary files", "*.bin")])
    if input_path:
        output_path = os.path.splitext(input_path)[0] + "_decompressed.txt"
        try:
            output_file = decompress_file(input_path, output_path)
            status = f"✅ Decompression Complete\n\n📄 File restored at: {output_file}"
            status_label.config(text=status)
            code_display.delete("1.0", END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

# ---------------- Run GUI ----------------

def run_gui():
    global code_display, status_label

    root = Tk()
    root.title("Huffman File Compressor")
    root.geometry("600x540")

    Label(root, text="Huffman File Compressor / Decompressor", font=("Helvetica", 16, "bold")).pack(pady=10)

    Button(root, text="Select File to Compress", command=select_file, width=30).pack(pady=5)
    Button(root, text="Select File to Decompress", command=select_file_to_decompress, width=30).pack(pady=5)

    status_label = Label(root, text="", fg="green", font=("Helvetica", 12, "bold"), wraplength=480, justify="left")
    status_label.pack(pady=5)

    Label(root, text="Generated Huffman Codes:", font=("Helvetica", 12)).pack(pady=(10, 5))

    frame = Frame(root)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

    scrollbar = Scrollbar(frame)
    scrollbar.pack(side=RIGHT, fill=Y)

    code_display = Text(frame, wrap="none", yscrollcommand=scrollbar.set, height=15)
    code_display.pack(fill=BOTH, expand=True)
    scrollbar.config(command=code_display.yview)

    root.mainloop()

# Start the GUI
run_gui()
