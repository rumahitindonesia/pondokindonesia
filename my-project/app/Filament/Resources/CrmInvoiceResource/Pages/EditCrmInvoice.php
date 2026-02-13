<?php

namespace App\Filament\Resources\CrmInvoiceResource\Pages;

use App\Filament\Resources\CrmInvoiceResource;
use Filament\Resources\Pages\EditRecord;

class EditCrmInvoice extends EditRecord
{
    protected static string $resource = CrmInvoiceResource::class;

    protected function getHeaderActions(): array
    {
        return [
            \Filament\Actions\DeleteAction::make(),
        ];
    }
}
