import unittest
import unittest.mock
import forest


class TestForestPlot(unittest.TestCase):
    def test_can_be_constructed(self):
        """the minimal information needed to construct a ForestPlot"""
        dataset = {
            "current_config": {
                "data_type_name": None
            }
        }
        model_run_time = None
        po1 = None
        figname = None
        plot_var = "plot_variable"
        conf1 = "current_config"
        reg1 = "current_region"
        rd1 = {
            "current_region": None
        }
        unit_dict = None
        unit_dict_display = None
        app_path = None
        init_time = None
        forest.plot.ForestPlot(dataset,
                               model_run_time,
                               po1,
                               figname,
                               plot_var,
                               conf1,
                               reg1,
                               rd1,
                               unit_dict,
                               unit_dict_display,
                               app_path,
                               init_time)

    def test_set_config(self):
        """minimal data needed to call set_config"""
        dataset = {
            "current_config": {
                "data_type_name": None
            },
            "new_config": {
                "data_type_name": "Label"
            }
        }
        model_run_time = None
        po1 = None
        figname = None
        plot_var = "plot_variable"
        conf1 = "current_config"
        reg1 = "current_region"
        rd1 = {
            "current_region": None
        }
        unit_dict = None
        unit_dict_display = None
        app_path = None
        init_time = None
        mock_plot = unittest.mock.Mock()
        with unittest.mock.patch("forest.plot.matplotlib") as matplotlib:
            forest_plot = forest.plot.ForestPlot(dataset,
                                                 model_run_time,
                                                 po1,
                                                 figname,
                                                 plot_var,
                                                 conf1,
                                                 reg1,
                                                 rd1,
                                                 unit_dict,
                                                 unit_dict_display,
                                                 app_path,
                                                 init_time)
            forest_plot.plot_funcs[plot_var] = mock_plot
            forest_plot.update_bokeh_img_plot_from_fig = unittest.mock.Mock()
            # System under test
            forest_plot.set_config("new_config")

            # Assertions
            forest_plot.update_bokeh_img_plot_from_fig.assert_called_once_with()
            mock_plot.assert_called_once_with()
            self.assertEqual(forest_plot.current_config, "new_config")
            self.assertEqual(forest_plot.plot_description, "Label")

    @unittest.skip("exploring forest architecture")
    @unittest.mock.patch("forest.plot.matplotlib")
    @unittest.mock.patch("forest.plot.bokeh")
    def test_forest_plot_calls_bokeh_plotting_figure(self,
                                                     bokeh,
                                                     matplotlib):
        """ForestPlot constructs its own bokeh.Figure instance

        .. note:: Every time create_plot() is called a call
                  to create_bokeh_img_plot_from_fig() inside
                  which bokeh.plotting.figure() is called

        .. warn:: ForestPlot does not initialise a reference
                  to self.current_figure that is done by
                  self.create_matplotlib_fig()

        .. note:: ForestPlot.create_matplotlib_fig() expects
                  self.current_var to be a key in self.plot_funcs

        .. note:: ForestPlot.get_image_array_from_figure() takes
                  a matplotlib.Figure instance
        """
        fixture = forest.plot.ForestPlot(*self.generic_args())
        fixture.plot_funcs["plot_variable"] = unittest.mock.Mock()
        fixture.create_matplotlib_fig()
        fixture.create_bokeh_img_plot_from_fig()
        bokeh.plotting.figure.assert_called_once_with()

    def test_forest_plot_should_accept_figure(self):
        """To open forest to allow generic layouts"""
        forest.plot.ForestPlot(*self.generic_args())

    def generic_args(self):
        """Helper to construct ForestPlot"""
        dataset = {
            "current_config": {
                "data_type_name": None
            }
        }
        model_run_time = None
        po1 = None
        figname = None
        plot_var = "plot_variable"
        conf1 = "current_config"
        reg1 = "current_region"
        rd1 = {
            "current_region": None
        }
        unit_dict = None
        unit_dict_display = None
        app_path = None
        init_time = None
        return (dataset,
                model_run_time,
                po1,
                figname,
                plot_var,
                conf1,
                reg1,
                rd1,
                unit_dict,
                unit_dict_display,
                app_path,
                init_time)
