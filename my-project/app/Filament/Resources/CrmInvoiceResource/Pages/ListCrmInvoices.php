<?php

namespace App\Filament\Resources\CrmInvoiceResource\Pages;

use App\Filament\Resources\CrmInvoiceResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListCrmInvoices extends ListRecords
{
    protected static string $resource = CrmInvoiceResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make()
                ->label('Tambah Invoice'),
        ];
    }
}
