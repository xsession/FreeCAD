#include <benchmark/benchmark.h>

static void BM_Recompute100Features(benchmark::State& state)
{
    for (auto _ : state) {
        benchmark::DoNotOptimize(state.iterations());
    }
}

BENCHMARK(BM_Recompute100Features);
BENCHMARK_MAIN();
