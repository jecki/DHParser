#!/usr/bin/env python3

def cpu_profile(func, repetitions=10):
    """Profile the function `func`.
    """
    import cProfile
    import pstats
    profile = cProfile.Profile()
    profile.enable()
    success = []
    for _ in range(repetitions):
        success = func()
        if not success:
            break
    profile.disable()
    # after your program ends
    stats = pstats.Stats(profile)
    stats.strip_dirs()
    stats.sort_stats('time').print_stats(80)
    return success

def main():
    from XMLParser import parsing
    xml_parser = parsing.factory()
    with open('testdata/test.xml', 'r', encoding='utf-8') as f:
        data = f.read()
    cpu_profile(lambda : xml_parser(data))


if __name__ == "__main__":
    main()