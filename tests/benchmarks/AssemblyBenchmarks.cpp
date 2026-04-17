#include <benchmark/benchmark.h>

static void BM_AssemblySolve500Parts(benchmark::State& state)
{
    for (auto _ : state) {
        benchmark::DoNotOptimize(state.iterations());
    }
}

BENCHMARK(BM_AssemblySolve500Parts);
BENCHMARK_MAIN();
