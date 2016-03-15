'use strict';

/**
 * @ngdoc directive
 * @name svenClientApp.directive:annotator
 * @description
 * # concepts
 */
angular.module('sven')
  .directive('annotator', function($log, $compile) {
    return {
      restrict : 'A',
      scope:{
        content: '=',
        filterByEntity: '&'
      },
      link : function(scope, element, attrs) {
        
        function checkEntity(event) {
          var entity = $(this).attr('data-content');
          $log.info('::annotator checkEntity', entity)
          scope.filterByEntity({entity: entity});
        };
        
        $(document).on('click', '.entity', checkEntity); 

        scope.$on("$destroy", function() {
          $log.info('::annotator @destroy')
          $(document).off('click', '.entity', checkEntity);
        
        });

        element.html(scope.content);
        $compile(element.contents())(scope);
      }
    }
  })