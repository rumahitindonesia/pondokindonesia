from django import forms
from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminSelectWidget

class GSheetSyncForm(forms.Form):
    spreadsheet_id = forms.CharField(
        label="Spreadsheet ID",
        help_text="ID spreadsheet dapat ditemukan di URL halaman Google Sheets Bapak (antara /d/ dan /edit).",
        required=True,
        widget=UnfoldAdminTextInputWidget(attrs={
            'placeholder': 'Contoh: 1abcXYZ-dst...',
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
        widget=UnfoldAdminSelectWidget()
    )
    sheet_name = forms.CharField(
        label="Nama Sheet (Opsional)",
        required=False,
        widget=UnfoldAdminTextInputWidget(attrs={
            'placeholder': 'Kosongkan jika ingin mengambil sheet pertama',
        })
    )
