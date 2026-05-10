from main import main as main_mod

def test_main_runs(capsys):
    main_mod.main()
    captured = capsys.readouterr()
    assert 'Initialization placeholder' in captured.out
