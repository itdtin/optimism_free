from app.quests.quests_flow.granary import granary
from app.quests.quests_flow.perp import perp
from app.quests.quests_flow.pika import pika
from app.quests.quests_flow.rubicon import rubicon
from app.quests.quests_flow.synapse import synapse
from app.quests.quests_flow.uni import uni
from app.quests.quests_flow.velodrome import velodrome

__all__ = [
    granary,
    perp,
    pika,
    rubicon,
    synapse,
    uni,
    velodrome,
]


def quests():
    return __all__
