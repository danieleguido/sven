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
            viewer = d3.select('.viewer'),
            svg = viewer
              .append("svg")
              .attr("height", 500)
              .attr("width", 500);

        // draw main line
        var axis = svg.append('path').attr({
          'fill': 'none',
          'stroke': '#b5b5b5'
        })


        var draw = function() {
          clearTimeout(timeout);
          var availableWidth = viewer[0][0].clientWidth;
          console.log(viewer[0][0], availableWidth)
          
          svg.attr({
            width: availableWidth
          });

          axis.attr({
            d: ['M', 20, 40, 'L', availableWidth-20, 40].join(' ')
          })
          

          console.log(scope.facets);
        };

        angular.element($window).bind('resize', function() {
          clearTimeout(timeout);
          timeout = setTimeout(draw, 200);
        });

        draw();

      }
    }
  })
