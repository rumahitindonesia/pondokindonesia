<?php

namespace App\Filament\Central\Resources\SettingResource\Pages;

use App\Filament\Central\Resources\SettingResource;
use App\Models\Setting;
use Filament\Actions;
use Filament\Resources\Pages\ManageRecords;
use Filament\Notifications\Notification;
use Illuminate\Support\Facades\Cache;

class ManageSettings extends ManageRecords
{
    protected static string $resource = SettingResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\Action::make('save')
                ->label('Save Settings')
                ->color('success')
                ->icon('heroicon-o-check-circle')
                ->action(function (array $data) {
                    foreach ($data as $key => $value) {
                        if ($value !== null && $value !== '') {
                            Setting::set($key, $value);
                        }
                    }

                    // Clear cache after saving
                    Cache::flush();

                    Notification::make()
                        ->title('Settings saved successfully')
                        ->success()
                        ->send();
                })
                ->form(fn () => SettingResource::form(\Filament\Forms\Form::make())->getComponents()),
        ];
    }

    public function mount(): void
    {
        parent::mount();
        
        // Load current settings into form
        $settings = Setting::all()->pluck('value', 'key')->toArray();
        $this->form->fill($settings);
    }
}
