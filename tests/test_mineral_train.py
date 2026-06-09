from models.mineral_classifier.train import train_stub


def test_train_stub_loss_decreases():
    history = train_stub(epochs=2, samples=10)
    assert len(history) == 2
    assert history[1] < history[0]
