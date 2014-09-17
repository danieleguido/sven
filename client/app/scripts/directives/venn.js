'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:venn
 * @description
 * # venn
 */
angular.module('svenClientApp')
  .directive('venn', function () {
    return {
      template: '<div class="viewer"></div>',
      restrict: 'E',
      scope: {
        data: '='
      },
      link: function postLink(scope, element, attrs) {
        
        var render = function(data) {
          // get positions for each set
          var sets = venn.venn(
            [{label: "A", size: 10}, {label: "B", size: 8}, {label: "C", size: 3}],
            [{sets: [0,1], size: 2}, {sets: [0,2], size: 0}, {sets: [1,2], size: 0}]
          );

            // draw the diagram in the 'simple_example' div
          venn.drawD3Diagram(d3.select(".viewer"), sets, 300, 300);
        }

        scope.$watch('data', function(data) {
          if(data)
            render(data)
        }, true);
      }
    };
  });
