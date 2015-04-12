'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # timeline directive. Create a comparative timeline visualisation from two series of date object:
 * [{day: 'YYY-MM-DD', count: 2}, {day: 'YYY-MM-DD', count: 1}...]
 * 
 */
 angular.module('sven')
  .directive('timeline', function ($log, $window) {
    return {
      template: '<div class="mouse tooltip">...</div><div class="viewer"></div>',
      restrict: 'EA',
      scope: {
        values: '=',
      },
      link: function postLink (scope, element, attrs) {
        $log.info(':: timeline');
        // on resize babe...
        var timeout, // draw() timeout on resize

            padding  = {
              v: 80, // padding for the line of the timeline
              h: 10
            },

            parseDate = d3.time.format("%Y-%m-%d").parse, // date parser function 

            viewer = d3.select('.viewer'),

            brush  = d3.svg.brush(), 

            svg = viewer
              .append("svg")
              .attr("height", 500),

            context = svg.append("g")
              .attr("class", "context")
              .attr("transform", "translate(" + padding.v + "," + padding.h + ")"),
            // draw main line
            axis = svg.append('path').attr({
              'fill': 'none',
              'stroke': '#b5b5b5',
              'stroke-width': 1
            });



        /*
          draw basic shapes
        */
        var lies = context
          .append("g")
            .attr("class", "values")

        context.append("g")
          .attr("class", "x brush")
          .call(brush)
            .selectAll("rect")
              .attr("y", 0)
              .attr("height", 30);

        brush.on("brush", function() {
          console.log("brushing babe", brush.extent())
        });

        var leftDate = svg.append('text')
              .attr({'class': 'label'}),
            rightDate = svg.append('text')
              .attr({'class': 'label'});

        var draw = function() {
          clearTimeout(timeout);
          if(!scope.values)
            return;
          var availableWidth = viewer[0][0].clientWidth,
              height = 30,
              values = scope.values.map(function (d) {
                d.date = parseDate(d.day).getTime();
                return d
              });
          /*
            update basic shapes
          */
          svg.attr({
            width: availableWidth
          });

          axis.attr({
            d: ['M', padding.v, 40, 'L', availableWidth - padding.v, 40].join(' ')
          });
          
          leftDate
            .attr({
              'text-anchor': 'end',
              transform: 'translate(' +  (padding.v - 15)+ ',30)'
            })
            .text(values[0].day)
            

          rightDate
            .attr({
              
              transform: 'translate(' + (availableWidth - padding.v + 15) +',30)'
            })
            .text(values[values.length-1].day);
          
          /*
            setting up min max and funcionts
          */
          var x = d3.time.scale().range([0, availableWidth - padding.v*2]),
              y = d3.scale.linear().range([height, 0]),

              min = 0,
              max_count = d3.max(scope.values, function (d) {
                console.log(d)
                return d.count;
              });

              // area = d3.svg.area()
              //   .interpolate("monotone")
              //   .x(function (d) { 
              //     console.log('data', d.date)
              //     return x(d.date);
              //   })
              //   .y0(height)
              //   .y1(function (d) {
              //     console.log('data', d.count)
              //     return y(d.count);
              //   });

          x.domain(d3.extent(values.map(function (d) {
            return d.date;
          })));

          y.domain([0, d3.max(values.map(function(d) {
            return d.count;
          }))]);

          brush.x(x);

          var selected = lies.selectAll('.value')
            .data(values, function(d) {
              return d.day// key to update
            })

          selected.enter().append('circle')
              .attr("r", 2)
              .attr({
                'class': 'value',
                cx: function (d) {
                  return x(d.date);
                },
                cy: function (d) {
                  return y(d.count);
                },
              });

          selected.attr({
                'class': 'value',
                cx: function (d) {
                  return x(d.date);
                },
                cy: function (d) {
                  return y(d.count);
                },
              });

          

          $log.info(':: timeline', max_count);
        };


        angular.element($window).bind('resize', function() {
          clearTimeout(timeout);
          timeout = setTimeout(draw, 200);
        });

        scope.$watch('values', function(val) {
          if(val)
            draw();
        });
        

      }
    }
  })
