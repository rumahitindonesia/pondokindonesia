<?php

namespace App\Filament\Central\Pages;

use App\Models\Setting;
use Filament\Forms\Components\Section;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;
use Filament\Forms\Form;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Illuminate\Support\Facades\Cache;

class AppSettings extends Page implements HasForms
{
    use InteractsWithForms;

    protected static ?string $navigationIcon = 'heroicon-o-cog-6-tooth';

    protected static string $view = 'filament.pages.settings'; // Using default filament view if possible, or custom if needed

    protected static ?string $navigationLabel = 'Application Settings';

    protected static ?string $title = 'Application Settings';

    protected static ?string $navigationGroup = 'System';

    public ?array $data = [];

    public function mount(): void
    {
        $this->form->fill([
            'starsender_api_key' => Setting::get('starsender_api_key'),
            'starsender_device_id' => Setting::get('starsender_device_id'),
            'gemini_api_key' => Setting::get('gemini_api_key'),
            'groq_api_key' => Setting::get('groq_api_key'),
            'unsplash_access_key' => Setting::get('unsplash_access_key'),
        ]);
    }

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Section::make('StarSender API (WhatsApp)')
                    ->description('Configuration for WhatsApp Notifications.')
                    ->schema([
                        TextInput::make('starsender_api_key')
                            ->label('API Key')
                            ->password()
                            ->revealable()
                            ->required(),
                        TextInput::make('starsender_device_id')
                            ->label('Device ID')
                            ->required(),
                    ])->columns(2),

                Section::make('AI Context Services')
                    ->description('Configuration for AI content and personalization.')
                    ->schema([
                        TextInput::make('groq_api_key')
                            ->label('Groq API Key')
                            ->password()
                            ->revealable()
                            ->helperText('Used for Llama 3 high-speed personalization.'),
                        TextInput::make('gemini_api_key')
                            ->label('Gemini API Key')
                            ->password()
                            ->revealable()
                            ->helperText('Managed by Google AI Studio.'),
                    ])->columns(2),

                Section::make('Visual Services')
                    ->description('Configuration for stock images.')
                    ->schema([
                        TextInput::make('unsplash_access_key')
                            ->label('Unsplash Access Key')
                            ->password()
                            ->revealable(),
                    ]),
            ])
            ->statePath('data');
    }

    protected function getFormActions(): array
    {
        return [
            \Filament\Actions\Action::make('save')
                ->label(__('filament-panels::resources/pages/edit-record.form.actions.save.label'))
                ->submit('save'),
        ];
    }

    public function save(): void
    {
        $data = $this->form->getState();

        foreach ($data as $key => $value) {
            Setting::set($key, $value);
        }

        Cache::flush();

        Notification::make()
            ->success()
            ->title('Settings saved successfully')
            ->send();
    }
}
