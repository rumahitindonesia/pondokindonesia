<?php
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Filament\Central\Resources\PostResource;
use Filament\Forms\Form;

try {
    echo "Testing PostResource::form()...\n";
    $livewire = new class extends \Livewire\Component implements \Filament\Forms\Contracts\HasForms {
        use \Filament\Forms\Concerns\InteractsWithForms;
        public function mount() { $this->form->fill(); }
    };
    
    $form = new Form($livewire);
    PostResource::form($form);
    echo "Form schema generated successfully.\n";
} catch (\Throwable $e) {
    echo "Error: " . $e->getMessage() . "\n";
    echo $e->getTraceAsString();
}
