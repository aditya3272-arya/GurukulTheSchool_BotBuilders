import customtkinter as ctk
from typing import List, Callable, Any

class DataTable(ctk.CTkScrollableFrame):
    def __init__(self, master, columns: List[str], on_edit: Callable = None, on_delete: Callable = None, **kwargs):
        super().__init__(master, **kwargs)
        self.columns = columns
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.data_rows = []
        
        self.grid_columnconfigure(list(range(len(columns) + 1)), weight=1)
        
        for i, col in enumerate(columns):
            header_label = ctk.CTkLabel(self, text=col, font=("Roboto", 14, "bold"))
            header_label.grid(row=0, column=i, padx=10, pady=10, sticky="w")
            
        action_header = ctk.CTkLabel(self, text="Actions", font=("Roboto", 14, "bold"))
        action_header.grid(row=0, column=len(columns), padx=10, pady=10, sticky="e")

    def set_data(self, data: List[dict]):
        for row_widgets in self.data_rows:
            for widget in row_widgets:
                widget.destroy()
        self.data_rows.clear()
        
        for row_idx, item in enumerate(data, start=1):
            row_widgets = []
            
            for col_idx, col in enumerate(self.columns):
                val = str(item.get(col, ""))
                if len(val) > 30:
                    val = val[:27] + "..."
                label = ctk.CTkLabel(self, text=val, anchor="w", justify="left")
                label.grid(row=row_idx, column=col_idx, padx=10, pady=5, sticky="w")
                row_widgets.append(label)
                
            action_frame = ctk.CTkFrame(self, fg_color="transparent")
            action_frame.grid(row=row_idx, column=len(self.columns), padx=10, pady=5, sticky="e")
            
            if self.on_edit:
                edit_btn = ctk.CTkButton(action_frame, text="Edit", width=60, 
                                         command=lambda i=item: self.on_edit(i))
                edit_btn.pack(side="left", padx=2)
                
            if self.on_delete:
                del_btn = ctk.CTkButton(action_frame, text="Delete", width=60, fg_color="#E74C3C", hover_color="#C0392B",
                                        command=lambda i=item: self.on_delete(i))
                del_btn.pack(side="left", padx=2)
                
            row_widgets.append(action_frame)
            self.data_rows.append(row_widgets)
