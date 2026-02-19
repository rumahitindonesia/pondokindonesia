from django import forms

class GSheetSyncForm(forms.Form):
    spreadsheet_id = forms.CharField(
        label="Spreadsheet ID",
        help_text="ID spreadsheet dapat ditemukan di URL halaman Google Sheets Bapak (antara /d/ dan /edit).",
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Contoh: 1abcXYZ-dst...',
            'class': 'border-base-300 dark:border-base-700 focus:ring-primary-500 focus:border-primary-500' 
            # Note: Unfold might add classes automatically via template helpers, 
            # but adding some defaults here is safe.
        })
    )
    model_type = forms.ChoiceField(
        label="Tujuan Data (Model)",
        choices=[
            ('lead', 'Leads / Calon Santri'),
            ('santri', 'Data Santri'),
            ('donatur', 'Data Donatur'),
            ('transaksi', 'Transaksi Donasi'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'border-base-300 dark:border-base-700 focus:ring-primary-500 focus:border-primary-500'
        })
    )
    sheet_name = forms.CharField(
        label="Nama Sheet (Opsional)",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Kosongkan jika ingin mengambil sheet pertama',
            'class': 'border-base-300 dark:border-base-700 focus:ring-primary-500 focus:border-primary-500'
        })
    )
