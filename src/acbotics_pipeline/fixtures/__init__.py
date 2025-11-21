print("Initializing Fixtures")
import acbotics_pipeline.fixtures.fixture

# import acbotics_pipeline.fixtures.fixture_kivy # causing args weirdness on import
import acbotics_pipeline.fixtures.fixture_pyplot


from acbotics_pipeline.fixtures.fixture import Fixture

# import acbotics_pipeline.fixtures.fixture_kivy # causing args weirdness on import
from acbotics_pipeline.fixtures.fixture_pyplot import Fixture_Pyplot
