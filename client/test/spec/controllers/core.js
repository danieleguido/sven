'use strict';

describe('Controller: CoreCtrl', function () {

  // load the controller's module
  beforeEach(module('svenClientApp'));

  var CoreCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function ($controller, $rootScope) {
    scope = $rootScope.$new();
    CoreCtrl = $controller('CoreCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function () {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
