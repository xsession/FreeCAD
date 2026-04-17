#include <benchmark/benchmark.h>

static void BM_STEPExport1000Faces(benchmark::State& state)
{
    for (auto _ : state) {
        benchmark::DoNotOptimize(state.iterations());
    }
}

BENCHMARK(BM_STEPExport1000Faces);
BENCHMARK_MAIN();
