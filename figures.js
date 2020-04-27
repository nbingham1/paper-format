var loadExampleFigure = function() {
	return new Promise(function(resolve, reject) {
	var data = {
		series: [
			[{x:1.5,  y:35.01, l:"s0p0"},
			 {x:3.25, y:23.17, l:"s0p1"},
			 {x:1.33, y:75.05, l:"s0p2"},
			 {x:0.42, y:12.62, l:"s0p3"},
			 {x:2.78, y:64.51, l:"s0p4"},
			 {x:3.02, y:24.20, l:"s0p5"},
			 {x:2.96, y:46.81, l:"s0p6"},
			 {x:1.95, y:34.52, l:"s0p7"}],
			[{x:0.90, y:146.76, l:"s1p0"}],
			[{x:2.13, y:198.34, l:"s2p0"}],
			[{x:3.20, y:197.62, l:"s3p0"},
			 {x:1.03, y:17.87, l:"s3p1"},
			 {x:2.52, y:28.07, l:"s3p2"},
			 {x:2.12, y:85.86, l:"s3p3"},
			 {x:1.53, y:67.81, l:"s3p4"}],
			[{x:2.64, y:172.00, l:"s4p0"}]
		]
	};
	
	var options = {
		showLine: false,
		chartPadding: {
			top: 40,
			right: 0,
			bottom: 40,
			left: 40
		},
		axisX: {
			type: Chartist.FixedScaleAxis,
			ticks: [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
			low: 0.0,
			high: 4.0,
			fullWidth: true
		},
		axisY: {
			type: Chartist.FixedScaleAxis,
			ticks: [0, 50, 100, 150, 200],
			low: 0,
			high: 200,
		},
		plugins: [
			Chartist.plugins.ctPointLabels({
				textAnchor: 'middle',
				labelKey: 'l'
			}),
			Chartist.plugins.ctAxisTitle({
				axisX: {
					axisTitle: 'X-Axis (Units)',
					axisClass: 'ct-axis-title',
					offset: {
						x: 0,
						y: 40
					},
					textAnchor: 'middle'
				},
				axisY: {
					axisTitle: 'Y-Axis (Units)',
					axisClass: 'ct-axis-title',
					offset: {
						x: 0,
						y: -20
					},
					textAnchor: 'middle',
					flipTitle: false
				}
			}),
  	]
	}

	Chart.create('.ct-chart#example-figure', data, options);
	if (resolve) {
		resolve();
	}
	});
}

