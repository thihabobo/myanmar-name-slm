# Laravel & PHP Integration Guide: Myanmar Name Semantic Matcher
> Seamless integration of Burglish & Ethnic phonetic matching into Laravel applications, EHR systems, and POS counters.

---

## 1. Overview

There are two primary ways to integrate the Myanmar Name Semantic Matcher into a Laravel backend:

| Method | Use Case | Latency | Dependency |
|---|---|---|---|
| **Option A: Pure Native PHP Service (`BurglishMatcher`)** | Instant autocomplete search & duplicate check in controllers / form requests. | **< 0.05 ms** | **Zero external dependencies** (Pure PHP 8.0+). Runs everywhere. |
| **Option B: FastAPI Microservice (`POST /match`)** | Enterprise multi-app deployments (web, mobile apps, POS counters). | **1 - 3 ms** | Requires running the Python microservice (`uvicorn src.api_server:app`). |

---

## 2. Option A: Pure Native PHP Service (Recommended for Zero-Latency)

The exact algorithm powering the Python phonetic normalizer is implemented as a pure PHP service at:  
[`App\Services\BurglishMatcher`](file:///home/bo/Projects/lagabar_hospital/app/Services/BurglishMatcher.php)

### Example 1: Comparing Two Patient Names in Controller
```php
use App\Services\BurglishMatcher;

$result = BurglishMatcher::compare('Kyaw Swar', 'Kyaw Zwar');

// Returns:
// [
//   'score'         => 0.95,
//   'is_duplicate'  => true,
//   'confidence'    => 'high',
//   'match_reasons' => ['Identical Burmese pronunciation (မြန်မာအသံထွက် တူညီပါသည်)'],
// ]
```

### Example 2: Filtering Eloquent Candidates for Autocomplete
```php
use App\Models\Patient;
use App\Services\BurglishMatcher;

public function searchPatients(Request $request)
{
    $query = trim($request->get('q', ''));
    if (strlen($query) < 2) return response()->json([]);

    // 1. Broad SQL pre-filter (by first 2 characters or soundex)
    $cleanQuery = BurglishMatcher::clean($query);
    $firstTwo = substr($cleanQuery, 0, 2);

    $patients = Patient::where('Status', 1)
        ->where(function($q) use ($query, $firstTwo) {
            $q->where('PatientName', 'like', "%{$firstTwo}%")
              ->orWhere('Phone', 'like', "%{$query}%")
              ->orWhere('PatientCode', 'like', "%{$query}%");
        })
        ->limit(30)
        ->get();

    // 2. Score and rank via BurglishMatcher
    $scored = $patients->map(function($patient) use ($query) {
        $match = BurglishMatcher::compare($query, $patient->PatientName);
        return [
            'patient'     => $patient,
            'score'       => $match['score'],
            'is_match'    => $match['is_duplicate'],
            'confidence'  => $match['confidence'],
            'reasons'     => $match['match_reasons'],
        ];
    })
    ->filter(fn($item) => $item['score'] >= 0.70)
    ->sortByDesc('score')
    ->values();

    return response()->json($scored);
}
```

---

## 3. Option B: FastAPI Microservice Integration

If you run the Python neural microservice on port 8000:

### Start the Microservice:
```bash
cd myanmar-name-slm
uvicorn src.api_server:app --host 0.0.0.0 --port 8000
```

### Call from Laravel via `Http` Facade:
```php
use Illuminate\Support\Facades\Http;

$response = Http::timeout(2)->post('http://127.0.0.1:8000/match', [
    'name1' => 'Nang Kham Noung',
    'name2' => 'Nan Hkam Naung',
]);

if ($response->successful()) {
    $data = $response->json();
    $isDup = $data['is_duplicate']; // true
    $score = $data['score'];        // 0.96
}
```

---

## 4. Ethnic Naming Examples Supported

| Scenario | Name 1 | Name 2 | Match Result |
|---|---|---|:---:|
| **Shan Dialectal Romanization** | `Nang Kham Noung` | `Nan Hkam Naung` | ✅ **Match (0.95)** |
| **Kayin S'gaw Spelling** | `Saw Eh Htoo` | `Saw Eh Htu` | ✅ **Match (0.95)** |
| **Chin Lineage Variation** | `Salai Lian Luai` | `Salai Liang Lway` | ✅ **Match (0.92)** |
| **Mon Historical Honorific** | `Nai Htaw Sorn` | `Min Htaw Sorn` | ✅ **Match (0.95)** |
| **Rakhine Regional Spelling** | `Khaing San Aung` | `Khine San Aung` | ✅ **Match (0.95)** |
| **Bamar Space-concatenation** | `Thu Zar` | `Thuzar` | ✅ **Match (0.98)** |
| **Honorific Stripping** | `U Kyaw Swar` | `Ko Kyaw Zwar` | ✅ **Match (0.95)** |
