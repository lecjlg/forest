import intake
from datetime import datetime
from collections import namedtuple

from forest import geo, gridded_forecast

URL = 'https://raw.githubusercontent.com/NCAR/intake-esm-datastore/master/catalogs/pangeo-cmip6.json'

def _load_from_intake(
    experiment_id='ssp585',
    table_id='Amon',
    grid_label='gn',
    variable_id='ta',
    institution_id='NCAR',
    activity_id='ScenarioMIP',
    parent_source_id='CESM2',
    member_id='r2i1p1f1'):
    collection = intake.open_esm_datastore(URL)
    print('opening catalogue')
    cat = collection.search(
        experiment_id=experiment_id,
        table_id=table_id,
        grid_label=grid_label,
        institution_id=institution_id,
        member_id=member_id,
        variable_id=variable_id)
    print('downloading data')
    dset_dict = cat.to_dataset_dict(
        zarr_kwargs={'consolidated': True, 'decode_times': False},
        cdf_kwargs={'chunks': {}, 'decode_times': False})
    ds_label = f'{activity_id}.{institution_id}.{parent_source_id}.{experiment_id}.{table_id}.{grid_label}'
    xr = dset_dict[ds_label]
    print(xr[variable_id])
    cube = xr[variable_id].to_iris()
    return cube[0] # drop member dimension


class IntakeLoader:
    def __init__(self):
        self._label = 'dummy data'
        self._cube = _load_from_intake()

    def image(self, state):
        # TODO: cube = ?
        cube = self._cube
        reference_time = datetime.now() # temporary
        variable = state.variable,
        init_time = state.initial_time,
        valid_time = state.valid_time,
        pressure = state.pressure

        cube = cube[0, 0, :, :] # TODO: replace with dynamic extract
        
        if cube is None:
            data = empty_image()
        else:
            data = geo.stretch_image(cube.coord('longitude').points,
                                     cube.coord('latitude').points, cube.data)
            data.update(gridded_forecast.coordinates(state.valid_time, state.initial_time,
                                    state.pressures, state.pressure))
            data.update({
                'name': [self._label],
                'units': [str(cube.units)]
            })
        return data


class Navigator:
    def __init__(self):
        self._cube = _load_from_intake()

    def variables(self):
        return 'air_temperature'

    def initial_times(self):
        cube = self._cube
        for cell in cube.coord('time').cells():
            return cell

    def valid_times(self):
        cube = self._cube
        return [cell.point for cell in cube.coord('time').cells()]

    def pressures(self):
        cube = self._cube
        pressures = []
        try:
            pressures = [cell.point for cell in cube.coord('air_pressure').cells()]
        except iris.exceptions.CoordinateNotFoundError:
            pass
        return pressures

if __name__ == '__main__':
    State = namedtuple('State', field_names=['variable', 'initial_time', 'valid_time', 'pressures', 'pressure'])
    state = State('temperature', datetime.now(), datetime.now(), [1,2,3], 1)
    
    dummy_loader = IntakeLoader()

    dummy_image = dummy_loader.image(state)

    print(dummy_image)

    print('PART 2')
    navigator = Navigator()
    print(navigator.variables())
    print(navigator.pressures())
    print(navigator.valid_times())
    print(navigator.initial_times())