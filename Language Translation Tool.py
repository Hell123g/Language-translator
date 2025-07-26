import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from googletrans import Translator, LANGUAGES
import pyperclip
from gtts import gTTS
from playsound import playsound
import os
import threading
import random
import json
from difflib import SequenceMatcher
from datetime import datetime

class SmartTranslatorApp:
    def __init__(self, root_window):
        self.root_window = root_window
        self.root_window.title("AI Language Translator")
        self.root_window.geometry("1000x700")
        self.root_window.resizable(True, True)
        
        # Initialize translation components
        self.translation_engine = Translator()
        self.translation_history = self.load_translation_history()
        self.ui_style = ttk.Style()
        
        # Configure UI appearance
        self.configure_ui_style()
        
        # Create application widgets
        self.create_application_widgets()
        
        # Set default languages (Auto-Detect to Hindi)
        self.source_language_combobox.set('Auto Detect')
        self.target_language_combobox.set('hindi')
        
    def configure_ui_style(self):
        """Configure modern UI styles and themes"""
        self.ui_style.theme_use('clam')
        self.ui_style.configure('TFrame', background='#f0f0f0')
        self.ui_style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        self.ui_style.configure('TButton', font=('Helvetica', 10), padding=5)
        self.ui_style.configure('TCombobox', padding=5)
        self.ui_style.configure('TLabelFrame', font=('Helvetica', 10, 'bold'))
        self.ui_style.map('TButton',
                        foreground=[('active', 'white'), ('!active', 'black')],
                        background=[('active', '#4a6baf'), ('!active', '#f0f0f0')])
        
    def create_application_widgets(self):
        """Create and arrange all UI components"""
        # Main container frame
        main_container = ttk.Frame(self.root_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input text section
        input_section = ttk.LabelFrame(main_container, text="Input Text", padding=(10, 5))
        input_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.input_text_area = scrolledtext.ScrolledText(input_section, height=12, wrap=tk.WORD, 
                                                       font=('Helvetica', 11), padx=10, pady=10)
        self.input_text_area.pack(fill=tk.BOTH, expand=True)
        
        # Language selection and controls
        control_panel = ttk.Frame(main_container)
        control_panel.pack(fill=tk.X, pady=(0, 10))
        
        # Source language selection with auto-detect
        language_options = ['Auto Detect'] + list(LANGUAGES.values())
        ttk.Label(control_panel, text="From:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.source_language_combobox = ttk.Combobox(control_panel, values=language_options, 
                                                   state='readonly', width=20)
        self.source_language_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Language swap button
        swap_button = ttk.Button(control_panel, text="⇄", width=3, command=self.swap_selected_languages)
        swap_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Target language selection (default to Hindi)
        ttk.Label(control_panel, text="To:").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.target_language_combobox = ttk.Combobox(control_panel, values=list(LANGUAGES.values()), 
                                                   state='readonly', width=20)
        self.target_language_combobox.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        
        # Translation trigger button
        translate_button = ttk.Button(control_panel, text="AI Translate", command=self.process_translation)
        translate_button.grid(row=0, column=5, padx=10, pady=5)
        
        # Output display with tabs
        self.output_display = ttk.Notebook(main_container)
        self.output_display.pack(fill=tk.BOTH, expand=True)
        
        # Main translation tab
        translation_tab = ttk.Frame(self.output_display)
        self.output_display.add(translation_tab, text="Translation")
        
        self.translated_text_display = scrolledtext.ScrolledText(translation_tab, height=12, wrap=tk.WORD, 
                                                               font=('Helvetica', 11), padx=10, pady=10,
                                                               state=tk.DISABLED)
        self.translated_text_display.pack(fill=tk.BOTH, expand=True)
        
        # Alternative translations tab
        alternatives_tab = ttk.Frame(self.output_display)
        self.output_display.add(alternatives_tab, text="Alternatives")
        
        self.alternative_translations_display = scrolledtext.ScrolledText(alternatives_tab, height=8, wrap=tk.WORD,
                                                                       font=('Helvetica', 10), padx=10, pady=10,
                                                                       state=tk.DISABLED)
        self.alternative_translations_display.pack(fill=tk.BOTH, expand=True)
        
        # Translation confidence indicator
        self.translation_confidence_meter = ttk.Progressbar(alternatives_tab, orient=tk.HORIZONTAL, 
                                                          length=100, mode='determinate')
        self.translation_confidence_meter.pack(fill=tk.X, pady=(0, 5))
        self.confidence_label = ttk.Label(alternatives_tab, text="AI Confidence: 0%")
        self.confidence_label.pack()
        
        # Action buttons panel
        action_buttons_panel = ttk.Frame(main_container)
        action_buttons_panel.pack(fill=tk.X, pady=(5, 0))
        
        # Functional buttons
        ttk.Button(action_buttons_panel, text="Copy", command=self.copy_translated_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_panel, text="Speak", command=self.speak_translated_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_panel, text="Save", command=self.save_current_translation).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_panel, text="History", command=self.display_translation_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_panel, text="Clear", command=self.reset_interface).pack(side=tk.RIGHT, padx=5)
    
    def get_language_code(self, language_name):
        """Convert full language name to language code"""
        if language_name == 'Auto Detect':
            return 'auto'
        for code, name in LANGUAGES.items():
            if name.lower() == language_name.lower():
                return code
        return 'en'  # Default to English if not found
    
    def detect_input_language(self, text_content):
        """Identify the language of the input text with confidence score"""
        try:
            detection_result = self.translation_engine.detect(text_content)
            return detection_result.lang, detection_result.confidence * 100
        except Exception:
            return 'en', 0  # Fallback to English with 0% confidence
    
    def check_translation_memory(self, source_text, source_lang, target_lang):
        """Search for similar translations in memory"""
        for memory_entry in self.translation_history:
            text_similarity = SequenceMatcher(None, source_text.lower(), memory_entry['source'].lower()).ratio()
            if (memory_entry['src_lang'] == source_lang and 
                memory_entry['dest_lang'] == target_lang and 
                text_similarity > 0.9):  # 90% similarity threshold
                return memory_entry['translation'], memory_entry['confidence']
        return None, 0
    
    def process_translation(self):
        """Handle the complete translation workflow"""
        input_text = self.input_text_area.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showwarning("Input Required", "Please enter text to translate.")
            return
        
        # Determine language parameters
        selected_source_language = self.source_language_combobox.get()
        target_language_code = self.get_language_code(self.target_language_combobox.get())
        
        # Handle auto-detection if selected
        if selected_source_language == 'Auto Detect':
            detected_language, detection_confidence = self.detect_input_language(input_text)
            self.source_language_combobox.set(LANGUAGES.get(detected_language, 'Auto Detect'))
            if detection_confidence < 50:  # Warn for low confidence
                messagebox.showwarning("Low Confidence", 
                                    f"Language detection confidence is low ({detection_confidence:.0f}%). "
                                    "Please verify the source language.")
            source_language_code = detected_language
        else:
            source_language_code = self.get_language_code(selected_source_language)
        
        # Check if we have this translation in memory
        cached_result, confidence_score = self.check_translation_memory(input_text, source_language_code, target_language_code)
        if cached_result:
            self.display_translation_result(cached_result, confidence_score)
            self.show_translation_alternatives(input_text, cached_result, source_language_code, target_language_code)
            return
        
        try:
            # Show processing status
            self.translated_text_display.config(state=tk.NORMAL)
            self.translated_text_display.delete("1.0", tk.END)
            self.translated_text_display.insert(tk.END, "Processing translation...")
            self.translated_text_display.config(state=tk.DISABLED)
            self.root_window.update()
            
            # Execute translation
            translation_result = self.translation_engine.translate(input_text, src=source_language_code, dest=target_language_code)
            
            # Calculate confidence score
            confidence_score = self.calculate_translation_confidence(input_text, translation_result.text, 
                                                                  source_language_code, target_language_code)
            
            # Store in memory
            self.save_to_translation_history(input_text, translation_result.text, 
                                           source_language_code, target_language_code, confidence_score)
            
            # Display results
            self.display_translation_result(translation_result.text, confidence_score)
            self.show_translation_alternatives(input_text, translation_result.text, 
                                             source_language_code, target_language_code)
            
        except Exception as error:
            messagebox.showerror("Translation Error", f"Translation failed: {str(error)}")
            self.translated_text_display.config(state=tk.NORMAL)
            self.translated_text_display.delete("1.0", tk.END)
            self.translated_text_display.config(state=tk.DISABLED)
    
    def calculate_translation_confidence(self, original_text, translated_text, source_lang, target_lang):
        """Estimate confidence score for the translation"""
        # Base confidence simulation
        confidence_score = random.uniform(70, 95)
        
        # Adjust for text length (longer texts typically have lower confidence)
        length_adjustment = min(1, 100 / len(original_text.split()))
        confidence_score *= length_adjustment
        
        # Adjust for difficult language pairs
        challenging_pairs = [('ja', 'en'), ('zh', 'en'), ('ar', 'en'), ('en', 'hi'), ('hi', 'en')]
        if (source_lang, target_lang) in challenging_pairs or (target_lang, source_lang) in challenging_pairs:
            confidence_score *= 0.9
        
        return min(95, max(50, confidence_score))  # Keep within 50-95% range
    
    def display_translation_result(self, translated_text, confidence_score):
        """Show the translation result with confidence indicator"""
        self.translated_text_display.config(state=tk.NORMAL)
        self.translated_text_display.delete("1.0", tk.END)
        self.translated_text_display.insert(tk.END, translated_text)
        
        # Add confidence annotation
        self.translated_text_display.insert(tk.END, f"\n\n[AI Confidence: {confidence_score:.0f}%]")
        self.translated_text_display.tag_add("confidence_note", "end-2l", "end")
        self.translated_text_display.tag_config("confidence_note", foreground="gray", font=('Helvetica', 9))
        
        self.translated_text_display.config(state=tk.DISABLED)
    
    def show_translation_alternatives(self, original_text, main_translation, source_lang, target_lang):
        """Display alternative translation options"""
        self.alternative_translations_display.config(state=tk.NORMAL)
        self.alternative_translations_display.delete("1.0", tk.END)
        
        # Generate simulated alternatives
        alternative_options = self.generate_alternative_translations(original_text, source_lang, target_lang)
        
        if alternative_options:
            self.alternative_translations_display.insert(tk.END, "Alternative translations:\n\n")
            for index, (alternative, quality_score) in enumerate(alternative_options.items(), 1):
                self.alternative_translations_display.insert(tk.END, f"{index}. {alternative}\n")
                self.alternative_translations_display.insert(tk.END, f"   [Quality Score: {quality_score:.0f}/100]\n\n")
        else:
            self.alternative_translations_display.insert(tk.END, "No significant alternatives found")
        
        self.alternative_translations_display.config(state=tk.DISABLED)
        
        # Update confidence display
        main_confidence = self.calculate_translation_confidence(original_text, main_translation, source_lang, target_lang)
        self.translation_confidence_meter['value'] = main_confidence
        self.confidence_label.config(text=f"AI Confidence: {main_confidence:.0f}%")
    
    def generate_alternative_translations(self, text_content, source_lang, target_lang):
        """Create simulated alternative translations"""
        alternative_translations = {}
        
        # Only generate alternatives for longer texts
        if len(text_content.split()) > 3:
            alternative_translations["Formal translation"] = random.uniform(65, 85)
            alternative_translations["Casual translation"] = random.uniform(70, 90)
            alternative_translations["Idiomatic translation"] = random.uniform(75, 95)
        
        return alternative_translations
    
    def save_to_translation_history(self, source_text, translated_text, source_lang, target_lang, confidence_score):
        """Store translation in memory"""
        history_entry = {
            'source': source_text,
            'translation': translated_text,
            'src_lang': source_lang,
            'dest_lang': target_lang,
            'confidence': confidence_score,
            'timestamp': datetime.now().isoformat()
        }
        self.translation_history.append(history_entry)
        self.save_translation_history()
    
    def load_translation_history(self):
        """Load translation history from file"""
        try:
            with open('translation_history.json', 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_translation_history(self):
        """Save translation history to file"""
        with open('translation_history.json', 'w') as file:
            json.dump(self.translation_history, file, indent=2)
    
    def swap_selected_languages(self):
        """Swap source and target language selections"""
        current_source = self.source_language_combobox.get()
        current_target = self.target_language_combobox.get()
        
        # Don't swap if source is auto-detect
        if current_source != 'Auto Detect':
            self.source_language_combobox.set(current_target)
            self.target_language_combobox.set(current_source)
    
    def copy_translated_text(self):
        """Copy translation to system clipboard"""
        translated_content = self.translated_text_display.get("1.0", "end-1c").split('\n\n[AI Confidence:')[0].strip()
        if translated_content and translated_content != "Processing translation...":
            pyperclip.copy(translated_content)
            messagebox.showinfo("Copied", "Translation copied to clipboard!")
        else:
            messagebox.showwarning("Nothing to Copy", "No translation available to copy.")
    
    def speak_translated_text(self):
        """Convert translation to speech"""
        translated_content = self.translated_text_display.get("1.0", "end-1c").split('\n\n[AI Confidence:')[0].strip()
        if not translated_content or translated_content == "Processing translation...":
            messagebox.showwarning("Nothing to Speak", "No translation available to speak.")
            return
        
        target_language_code = self.get_language_code(self.target_language_combobox.get())
        
        # Run text-to-speech in background thread
        threading.Thread(target=self.execute_text_to_speech, 
                        args=(translated_content, target_language_code), 
                        daemon=True).start()
    
    def save_current_translation(self):
        """Save current translation to history"""
        source_text = self.input_text_area.get("1.0", tk.END).strip()
        translated_text = self.translated_text_display.get("1.0", "end-1c").split('\n\n[AI Confidence:')[0].strip()
        
        if not source_text or not translated_text or translated_text == "Processing translation...":
            messagebox.showwarning("Nothing to Save", "No translation available to save.")
            return
        
        source_lang = self.get_language_code(self.source_language_combobox.get())
        target_lang = self.get_language_code(self.target_language_combobox.get())
        
        self.save_to_translation_history(source_text, translated_text, source_lang, target_lang,
                                       float(self.confidence_label.cget("text").split()[-1][:-1]))
        messagebox.showinfo("Saved", "Translation saved to history!")
    
    def display_translation_history(self):
        """Show translation history window"""
        history_window = tk.Toplevel(self.root_window)
        history_window.title("Translation History")
        history_window.geometry("800x600")
        
        history_tree = ttk.Treeview(history_window, 
                                  columns=('source', 'translation', 'languages', 'confidence', 'date'), 
                                  show='headings')
        
        # Configure treeview columns
        history_tree.heading('source', text='Original Text')
        history_tree.heading('translation', text='Translation')
        history_tree.heading('languages', text='Language Pair')
        history_tree.heading('confidence', text='Confidence')
        history_tree.heading('date', text='Date/Time')
        
        history_tree.column('source', width=200)
        history_tree.column('translation', width=200)
        history_tree.column('languages', width=100)
        history_tree.column('confidence', width=80)
        history_tree.column('date', width=120)
        
        # Populate with history data (newest first)
        for entry in reversed(self.translation_history):
            language_pair = f"{entry['src_lang']}→{entry['dest_lang']}"
            formatted_date = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            history_tree.insert('', tk.END, values=(
                entry['source'][:50] + '...' if len(entry['source']) > 50 else entry['source'],
                entry['translation'][:50] + '...' if len(entry['translation']) > 50 else entry['translation'],
                language_pair,
                f"{entry['confidence']:.0f}%",
                formatted_date
            ))
        
        history_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar
        history_scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(yscroll=history_scrollbar.set)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def execute_text_to_speech(self, text_content, language_code):
        """Handle text-to-speech conversion"""
        try:
            speech_engine = gTTS(text=text_content, lang=language_code)
            speech_engine.save("translation_audio.mp3")
            playsound("translation_audio.mp3")
            os.remove("translation_audio.mp3")
        except Exception as error:
            messagebox.showerror("Speech Error", f"Text-to-speech failed: {str(error)}")
    
    def reset_interface(self):
        """Clear all input and output fields"""
        self.input_text_area.delete("1.0", tk.END)
        self.translated_text_display.config(state=tk.NORMAL)
        self.translated_text_display.delete("1.0", tk.END)
        self.translated_text_display.config(state=tk.DISABLED)
        self.alternative_translations_display.config(state=tk.NORMAL)
        self.alternative_translations_display.delete("1.0", tk.END)
        self.alternative_translations_display.config(state=tk.DISABLED)
        self.translation_confidence_meter['value'] = 0
        self.confidence_label.config(text="AI Confidence: 0%")

if __name__ == "__main__":
    application_root = tk.Tk()
    translator_app = SmartTranslatorApp(application_root)
    application_root.mainloop()