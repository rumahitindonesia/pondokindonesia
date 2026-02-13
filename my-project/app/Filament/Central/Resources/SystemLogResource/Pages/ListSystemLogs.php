<?php

namespace App\Filament\Central\Resources\SystemLogResource\Pages;

use App\Filament\Central\Resources\SystemLogResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListSystemLogs extends ListRecords
{
    protected static string $resource = SystemLogResource::class;

    protected function getHeaderActions(): array
    {
        return [
            // No create action for logs
        ];
    }
}
