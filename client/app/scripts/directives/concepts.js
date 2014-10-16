'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:concepts
 * @description
 * # concepts
 */
angular.module('svenClientApp')
  .directive('concepts', function () {
    return {
      template: '<div class="mouse tooltip">...</div><div class="viewer"></div>',
      restrict: 'E',
      scope: {
        data: '=',
        measure: '=',
        groups: '='
      },
      link: function postLink(scope, element, attrs) {
        var tooltip = d3.select("div.tooltip.mouse"),
            matrix   = snark
              .matrix()
              .init(d3.select(".viewer"));
        
        $('.viewer').on('scroll', function(e){
          matrix.onscroll({
            left: $(this).scrollLeft()
          });
        }).on("mouseenter", "circle", function() {
          if(!scope.data) return;
          tooltip
            .style("opacity", 1)
            .text('ciao');
          
        }).on("mousemove", "circle", function(event) {
          tooltip
            .style("opacity", 1)
            .style("left", Math.max(0, event.offsetX) +  "px")
            .style("top", (event.pageY - 10) + "px");
        }).on("mouseleave",  "circle", function() {
          tooltip
            .style("opacity", 0)
          });

        var render = function() {
          // get positions for each set
        
          if(scope.data)
            matrix
              .headers(scope.groups)
              .data(scope.data, function(d) {return d.cluster;})
              .update({ measure:scope.measure||'tf'})
          
        }



        scope.$watch('data', render, true);

        scope.$watch('measure', render, true);
      }
    };
  });
