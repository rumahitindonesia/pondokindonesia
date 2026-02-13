<?php

namespace App\Filament\Pages;

use App\Models\TenantSetting;
use Filament\Forms\Components\Section;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Form;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Filament\Actions\Action;

class ManageSettings extends Page
{
    protected static ?string $navigationIcon = 'heroicon-o-cog-6-tooth';

    protected static string $view = 'filament.pages.manage-settings';

    protected static ?string $title = 'Pengaturan';

    protected static ?string $navigationLabel = 'Pengaturan';
    
    protected static ?string $slug = 'settings';

    public ?array $data = [];

    public function mount(): void 
    {
        $this->form->fill([
            'unsplash_access_key' => TenantSetting::get('unsplash_access_key'),
        ]);
    }

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Section::make('Unsplash Integration')
                    ->description('Konfigurasi API Key untuk fitur pencarian gambar otomatis.')
                    ->schema([
                        TextInput::make('unsplash_access_key')
                            ->label('Unsplash Access Key')
                            ->password()
                            ->revealable()
                            ->required()
                            ->helperText('Dapatkan Access Key di https://unsplash.com/developers'),
                    ]),
            ])
            ->statePath('data');
    }

    public function save(): void
    {
        $data = $this->form->getState();

        TenantSetting::set('unsplash_access_key', $data['unsplash_access_key']);

        Notification::make() 
            ->success()
            ->title('Pengaturan berhasil disimpan')
            ->send();
    }

    protected function getFormActions(): array
    {
        return [
            Action::make('save')
                ->label('Simpan Perubahan')
                ->submit('save'),
        ];
    }
}
