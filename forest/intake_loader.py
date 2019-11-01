'''
Module for loading data from the Pangeo CMIP6n intake catalogue (usng the intake-esm
loader) created by NCAR.
'''

from datetime import datetime
from collections import namedtuple
import functools

import bokeh
import intake
import iris
import numpy

from forest import geo, gridded_forecast

# Location of the Pangeo-CMIP6 intake catalogue file.
URL = 'https://raw.githubusercontent.com/NCAR/intake-esm-datastore/master/catalogs/pangeo-cmip6.json'

def _get_intake_vars(
        experiment_id,
        table_id,
        grid_label,
        institution_id,
        member_id):
    collection = intake.open_esm_datastore(URL)
    cat = collection.search(
        experiment_id=experiment_id,
        table_id=table_id,
        grid_label=grid_label,
        institution_id=institution_id,
        member_id=member_id,
    )
    var_list = cat.unique('variable_id')['variable_id']['values']
    return var_list


@functools.lru_cache(maxsize=16)
def _load_from_intake(
        experiment_id,
        table_id,
        grid_label,
        variable_id,
        institution_id,
        activity_id,
        member_id):
    """
    Load data from the pangeo CMIP6 intake catalogue.The arguments relate to
    the CMIP6 parameters of a dataset. The CMIP6 reference is the ESGF servers
    which can be accessed here:
    https://esgf-index1.ceda.ac.uk/search/cmip6-ceda/

    """
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
    try:
        parent_source_id = [l1 for l1 in dset_dict.values()][0].parent_source_id
    except IndexError:
        import pdb
        pdb.set_trace()
    ds_label = f'{activity_id}.{institution_id}.{parent_source_id}.{experiment_id}.{table_id}.{grid_label}'
    xr = dset_dict[ds_label]
    print(xr[variable_id])
    cube = xr[variable_id].to_iris()

    coord_names = [c1.name() for c1 in cube.coords()]
    if 'air_pressure' in coord_names:
        cube.coord('air_pressure').convert_units('hPa')
    return cube[0]  # drop member dimension


class IntakeView(object):
    def __init__(self, loader, color_mapper):
        self.loader = loader
        self.color_mapper = color_mapper
        self.source = bokeh.models.ColumnDataSource({
            "x": [],
            "y": [],
            "dw": [],
            "dh": [],
            "image": []})

    def render(self, state):
        self.source.data = self.loader.image(state)

    def add_figure(self, figure):
        renderer = figure.image(
            x="x",
            y="y",
            dw="dw",
            dh="dh",
            image="image",
            source=self.source,
            color_mapper=self.color_mapper)
        tool = bokeh.models.HoverTool(
            renderers=[renderer],
            tooltips=[
                ("Name", "@name"),
                ("Value", "@image @units"),
                ('Valid', '@valid{%F %H:%M}'),
                ("Level", "@level"),
                ("Experiment", "@experiment"),
                ("Institution", "@institution"),
                ("Member", "@memberid"),
                ('Variable', "@variableid"),
            ],
            formatters={
                'valid': 'datetime',
            })
        figure.add_tools(tool)
        return renderer


@functools.lru_cache(maxsize=16)
def _get_bokeh_image(cube,
                     experiment_id,
                     variable_id,
                     institution_id,
                     initial_time,
                     member_id,
                     selected_time,
                     pressure,
                     ):


    def time_comp(select_time, time_cell):  #
        data_time = gridded_forecast._to_datetime(time_cell.point)
        try:
            if abs((select_time - data_time).days) < 2:
                return True
        except ValueError:
            pass
        return False

    def lat_filter(lat):
        """
        Due to the way the current projection of gridded data works, the poles are
        not well handled, resulting in NaNs if we use the full range of latitudes.
        The current hack is to chop off latitude greater than 85 degrees north and
        south. Given the importance of data at the poles in climate change research,
        we will need to fix this in future.
        """
        return -85.0 < lat < 85.0

    def pressure_select(select_pressure, data_pressure):
        return abs(select_pressure - data_pressure.point) < 1.0

    if cube is None or initial_time is None:
        data = gridded_forecast.empty_image()
    else:
        constraint_dict = {'time': functools.partial(time_comp,
                                                     selected_time),
                           'latitude': lat_filter,
                           }
        coord_names = [c1.name() for c1 in cube.coords()]
        if 'air_pressure' in coord_names:
            constraint_dict['air_pressure'] = functools.partial(
                pressure_select,
                pressure,
            )
        cube_cropped = cube.extract(iris.Constraint(**constraint_dict))
        lat_pts = cube_cropped.coord('latitude').points
        long_pts = cube_cropped.coord('longitude').points - 180.0
        cube_data_cropped = cube_cropped.data
        cube_width = int(cube_data_cropped.shape[1] / 2)
        cube_data_cropped = numpy.concatenate(
            [cube_data_cropped[:, cube_width:],
             cube_data_cropped[:, :cube_width]], axis=1)

        data = geo.stretch_image(long_pts, lat_pts, cube_data_cropped)
        data['image'] = [numpy.ma.masked_array(data['image'][0],
                                               mask=numpy.isnan(
                                                   data['image'][0]))]
        return data

class IntakeLoader:
    def __init__(self, pattern):
        institution_id, experiment_id,member_id, grid, table_id,activity_id = pattern.split('_')
        self.experiment_id = experiment_id
        self.table_id = table_id
        self.grid_label = grid
        self.variable_id = 'ta'
        self.institution_id = institution_id
        self.activity_id = activity_id
        self.member_id = member_id
        self._label = f'{self.experiment_id}_{self.institution_id}_{self.member_id}'
        self._cube = _load_from_intake(experiment_id=self.experiment_id,
                                       table_id=self.table_id,
                                       grid_label=self.grid_label,
                                       variable_id=self.variable_id,
                                       institution_id=self.institution_id,
                                       activity_id=self.activity_id,
                                       member_id=self.member_id)



    def image(self, state):
        """
        Main image loading function. This function will actually realise the
        data,
        """
        do_update = False
        if self.variable_id != state.variable:
            self.variable_id = state.variable
            do_update = True

        if do_update:
            self._cube = _load_from_intake(experiment_id=self.experiment_id,
                                           table_id=self.table_id,
                                           grid_label=self.grid_label,
                                           variable_id=self.variable_id,
                                           institution_id=self.institution_id,
                                           activity_id=self.activity_id,
                                           member_id=self.member_id)

        valid_time = state.valid_time
        pressure = state.pressure

        selected_time = gridded_forecast._to_datetime(valid_time)

        # the guts of creating the bokeh object has been put into a separate
        # function so that it can be cached, so if image is called multiple
        # time the calculations are only done once (hopefully).
        data = _get_bokeh_image(self._cube, self.experiment_id,
                                self.variable_id,
                                self.institution_id, state.initial_time,
                                self.member_id, selected_time, pressure)

        data.update(gridded_forecast.coordinates(str(selected_time),
                                                 state.initial_time,
                                                 state.pressures,
                                                 pressure))
        data.update({
            'name': [self._label],
            'units': [str(self._cube.units)],
            'experiment': [self.experiment_id],
            'institution': [self.institution_id],
            'memberid': [self.member_id],
            'variableid': [self.variable_id]
        })

        return data


class Navigator:
    def __init__(self):
        self.experiment_id = 'ssp585'
        self.table_id = 'Amon'
        self.grid_label = 'gn'
        self.variable_id = 'ta'
        self.institution_id = 'NCAR'
        self.activity_id = 'ScenarioMIP'
        self.parent_source_id = 'CESM2'
        self.member_id = 'r2i1p1f1'
        self._label = f'{self.experiment_id}_{self.institution_id}_{self.member_id}'
        self._cube = _load_from_intake(experiment_id=self.experiment_id,
                                       table_id=self.table_id,
                                       grid_label=self.grid_label,
                                       variable_id=self.variable_id,
                                       institution_id=self.institution_id,
                                       activity_id=self.activity_id,
                                       member_id=self.member_id)
        self._cube.coord('air_pressure').convert_units('hPa')

    def variables(self, pattern):
        return ['ta'] + _get_intake_vars(experiment_id=self.experiment_id,
                                table_id=self.table_id,
                                grid_label=self.grid_label,
                                institution_id=self.institution_id,
                                member_id=self.member_id)

    def initial_times(self, pattern, variable=None):
        cube = self._cube
        for cell in cube.coord('time').cells():
            init_time = gridded_forecast._to_datetime(cell.point)
            return [init_time]

    def valid_times(self, pattern, variable, initial_time):
        cube = self._cube
        valid_times = [gridded_forecast._to_datetime(cell.point) for cell in
                       cube.coord('time').cells()]
        return valid_times

    def pressures(self, pattern, variable, initial_time):
        cube = self._cube
        pressures = []
        try:
            pressures = [cell.point for cell in
                         cube.coord('air_pressure').cells()]
        except iris.exceptions.CoordinateNotFoundError:
            pass
        return pressures


if __name__ == '__main__':
    State = namedtuple('State',
                       field_names=['variable', 'initial_time', 'valid_time',
                                    'pressures', 'pressure'])
    state = State('temperature', datetime.now(), datetime.now(), [1, 2, 3], 1)

    dummy_loader = IntakeLoader()

    dummy_image = dummy_loader.image(state)

    print(dummy_image)

    print('PART 2')
    navigator = Navigator()
    print(navigator.variables())
    print(navigator.pressures())
    print(navigator.valid_times())
    print(navigator.initial_times())
