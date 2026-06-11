import 'package:flutter/material.dart';

import '../services/terraforge_api.dart';
import '../widgets/backend_action_screen.dart';

class HydrogeologyScreen extends StatelessWidget {
  const HydrogeologyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final api = TerraforgeApi();
    return BackendActionScreen(
      title: 'Hydrogeology',
      description: 'Load groundwater table and borehole records from the API.',
      actionLabel: 'Load Hydro Data',
      onAction: () async {
        final table = await api.groundwaterTable();
        final boreholes = await api.boreholes();
        return {'groundwater_table': table, 'boreholes': boreholes};
      },
    );
  }
}
