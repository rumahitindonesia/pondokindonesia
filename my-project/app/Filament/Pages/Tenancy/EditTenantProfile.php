<?php

namespace App\Filament\Pages\Tenancy;

use Filament\Forms\Components\FileUpload;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Form;
use Filament\Pages\Tenancy\EditTenantProfile as BaseEditTenantProfile;
use Illuminate\Support\Facades\Auth;

class EditTenantProfile extends BaseEditTenantProfile
{
    public static function getLabel(): string
    {
        return 'Profil Lembaga';
    }

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                TextInput::make('name')
                    ->label('Nama Lembaga')
                    ->required()
                    ->disabled(!Auth::user()->hasRole('Admin Tenant')),
                FileUpload::make('logo_path')
                    ->label('Logo Lembaga')
                    ->image()
                    ->directory('tenant-logos')
                    ->disabled(!Auth::user()->hasRole('Admin Tenant')),
                Textarea::make('description')
                    ->label('Deskripsi')
                    ->rows(3)
                    ->disabled(!Auth::user()->hasRole('Admin Tenant')),
                Textarea::make('address')
                    ->label('Alamat Lengkap')
                    ->rows(3)
                    ->disabled(!Auth::user()->hasRole('Admin Tenant')),
            ]);
    }
}
